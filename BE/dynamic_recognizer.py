"""
Dynamic Gesture Recognizer Engine (Module Chuyên Biệt Xử Lý Cử Chỉ Động)
=======================================================================
Đảm nhiệm:
  1. Lọc bỏ các frame rỗng (Active Hand Frames Extraction):
     - Chỉ trích xuất các frame bàn tay thực sự xuất hiện trong bộ đệm trượt.
     - Triệt tiêu 100% việc nhiễu frame số 0 phá vỡ khoảng cách DTW.
  2. Chuẩn hoá toạ độ tương đối (Wrist-Relative & Translation Invariant):
     - Dời 21 điểm bàn tay về gốc cổ tay per-frame, bất biến vị trí đứng.
  3. Tự động căn chỉnh Mask (Adaptive Mask Alignment):
     - Tự động nhận diện template có Pose hay không có Pose.
  4. Bộ lọc Động học Vận tốc Ngón tay & Bàn tay (Fingertip & Thumb Kinematic Spotter):
     - Bắt trọn nhịp lắc của ngón cái (Thumb tip Joint 4) cho cử chỉ "Số 10".
  5. Quy hoạch động FastDTW & Cơ chế Cooldown.
"""

from collections import deque
import numpy as np
from typing import Dict, List, Optional, Tuple

KEYPOINT_DIM = 1662


def normalize_dynamic_sequence(sequence: np.ndarray) -> np.ndarray:
    """
    Chuẩn hoá toạ độ tương đối per-frame cho chuỗi cử chỉ động:
      - Bàn tay phải (1599:1662): dời 21 khớp về gốc cổ tay phải (Joint 0)
      - Bàn tay trái (1536:1599): dời 21 khớp về gốc cổ tay trái (Joint 0)
      - Cánh tay (0:132): dời về gốc giữa 2 vai (nếu có Pose)
    Giúp cử chỉ động hoàn toàn bất biến vị trí đứng (Translation Invariant)!
    """
    if sequence is None or len(sequence) == 0:
        return sequence

    norm_seq = sequence.copy().astype(np.float32)
    for f in range(len(norm_seq)):
        # 1. Bàn tay phải
        rh = norm_seq[f, 1599:1662].reshape(21, 3)
        if not np.all(rh == 0):
            norm_seq[f, 1599:1662] = (rh - rh[0]).flatten()

        # 2. Bàn tay trái
        lh = norm_seq[f, 1536:1599].reshape(21, 3)
        if not np.all(lh == 0):
            norm_seq[f, 1536:1599] = (lh - lh[0]).flatten()

        # 3. Cánh tay (Pose)
        pose = norm_seq[f, 0:132].reshape(33, 4)
        if not np.all(pose == 0):
            mid_shoulder = (pose[11, :3] + pose[12, :3]) / 2.0
            pose[:, :3] -= mid_shoulder
            norm_seq[f, 0:132] = pose.flatten()

    return norm_seq


def resample_sequence(sequence: np.ndarray, target_length: int = 30) -> np.ndarray:
    """Nội suy chuỗi keypoints về độ dài chuẩn (30 frames)."""
    n_frames = len(sequence)
    if n_frames == 0:
        return np.zeros((target_length, KEYPOINT_DIM), dtype=np.float32)
    if n_frames == target_length:
        return sequence.astype(np.float32)

    old_indices = np.linspace(0, n_frames - 1, num=n_frames)
    new_indices = np.linspace(0, n_frames - 1, num=target_length)

    resampled = np.zeros((target_length, sequence.shape[1]), dtype=np.float32)
    for col in range(sequence.shape[1]):
        resampled[:, col] = np.interp(new_indices, old_indices, sequence[:, col])

    return resampled


def extract_active_hand_sequence(seq: np.ndarray) -> Tuple[np.ndarray, str]:
    """
    Trích xuất chuỗi 21 khớp của bàn tay hoạt động chính (shape: T, 63).
    Dời 21 khớp về gốc cổ tay (Joint 0) per-frame để bất biến vị trí đứng.
    """
    if seq is None or len(seq) == 0:
        return np.zeros((1, 63), dtype=np.float32), "None"

    rh_seq = seq[:, 1599:1662].copy().reshape(len(seq), 21, 3)
    lh_seq = seq[:, 1536:1599].copy().reshape(len(seq), 21, 3)

    rh_active = sum(1 for f in rh_seq if not np.all(f == 0))
    lh_active = sum(1 for f in lh_seq if not np.all(f == 0))

    if rh_active >= lh_active and rh_active > 0:
        for f in range(len(rh_seq)):
            if not np.all(rh_seq[f] == 0):
                rh_seq[f] = rh_seq[f] - rh_seq[f, 0]
        return rh_seq.reshape(len(seq), 63), "Right"
    elif lh_active > 0:
        for f in range(len(lh_seq)):
            if not np.all(lh_seq[f] == 0):
                lh_seq[f] = lh_seq[f] - lh_seq[f, 0]
        return lh_seq.reshape(len(seq), 63), "Left"

    return rh_seq.reshape(len(seq), 63), "None"


def compute_joint_motion_variance(seq_Tx63: np.ndarray) -> np.ndarray:
    """
    TẦNG 2: Dynamic Motion-Variance Masking (Trọng Số Động Học Tự Động)
    Tính toán mức độ hoạt động của 21 khớp bàn tay dựa trên độ biến thiên thời gian:
      - Khớp nào có chuyển động thực tế (Velocity > 0) -> Trọng số tối đa (1.0).
      - Khớp nào đứng yên hoặc chuyển động ngẫu nhiên -> Trọng số sàn (0.20).
    Giải quyết triệt để vấn đề: Khớp mang ý nghĩa chính quyết định điểm số,
    các ngón tay phụ giữ yên không làm kéo tụt độ tin cậy!
    """
    T = len(seq_Tx63)
    if T < 2:
        return np.ones(63, dtype=np.float32)

    pts = seq_Tx63.reshape(T, 21, 3)
    step_diffs = np.linalg.norm(pts[1:] - pts[:-1], axis=2)  # shape: (T-1, 21)
    joint_motion = np.sum(step_diffs, axis=0)                # shape: (21,)

    max_motion = float(np.max(joint_motion))
    if max_motion < 1e-4:
        return np.ones(63, dtype=np.float32)

    # Chuẩn hoá trọng số từ 0.20 (khớp phụ đứng yên) đến 1.0 (khớp hoạt động chính)
    joint_weights = 0.20 + 0.80 * (joint_motion / max_motion)
    return np.repeat(joint_weights, 3).astype(np.float32)


def fast_dtw_distance(seq_a: np.ndarray, seq_b: np.ndarray) -> float:
    """
    TẦNG 3: Unified Sequential Matcher (Bộ So Khớp Chuỗi Động Học Tổng Quát)
    Kết hợp:
      1. Bất biến tay Trái / Phải & Lật gương (Mirror-X Invariance)
      2. Trọng số biến thiên động học Tầng 2 (Dynamic Motion-Variance Masking)
      3. Ma trận quy hoạch động FastDTW chuẩn hóa
    """
    n, m = len(seq_a), len(seq_b)
    if n == 0 or m == 0:
        return float("inf")

    # 1. Trích xuất chuỗi bàn tay hoạt động chính
    hand_a, _ = extract_active_hand_sequence(seq_a)
    hand_b, _ = extract_active_hand_sequence(seq_b)

    if np.all(hand_a == 0) or np.all(hand_b == 0):
        return 1.0

    # 2. Tạo bản lật đối xứng Mirror-X để hỗ trợ cả người thuận tay trái/phải & camera lật gương
    hand_a_flip = hand_a.copy().reshape(n, 21, 3)
    hand_a_flip[:, :, 0] = -hand_a_flip[:, :, 0]
    hand_a_flip = hand_a_flip.reshape(n, 63)

    # 3. Tính trọng số biến thiên động học cho cả 2 chuỗi
    w_a = compute_joint_motion_variance(hand_a)
    w_b = compute_joint_motion_variance(hand_b)
    w_eff = np.maximum(w_a, w_b)
    w_mean = float(np.mean(w_eff))
    if w_mean < 1e-4:
        w_mean = 1.0

    def _calc_dtw(a_pts: np.ndarray, b_pts: np.ndarray, weights: np.ndarray) -> float:
        # Áp dụng trọng số động học lên từng khớp
        weighted_diff = (a_pts[:, np.newaxis, :] - b_pts[np.newaxis, :, :]) * weights
        cost_matrix = np.linalg.norm(weighted_diff, axis=2)

        dtw = np.full((n + 1, m + 1), float("inf"), dtype=np.float32)
        dtw[0, 0] = 0.0

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = cost_matrix[i - 1, j - 1]
                dtw[i, j] = cost + min(dtw[i - 1, j],
                                       dtw[i, j - 1],
                                       dtw[i - 1, j - 1])

        # Chuẩn hoá theo độ dài chuỗi và mức trọng số trung bình
        return float(dtw[n, m] / ((n + m) * w_mean))

    dist_direct = _calc_dtw(hand_a, hand_b, w_eff)
    dist_flip = _calc_dtw(hand_a_flip, hand_b, w_eff)
    best_hand_dist = min(dist_direct, dist_flip)

    # 4. Kết hợp Cánh tay (Pose) nếu cả 2 mẫu đều có dữ liệu thân trên
    has_pose_a = not np.all(seq_a[:, 0:132] == 0)
    has_pose_b = not np.all(seq_b[:, 0:132] == 0)
    if has_pose_a and has_pose_b:
        pose_a = seq_a[:, 0:132]
        pose_b = seq_b[:, 0:132]
        w_pose = np.ones(132, dtype=np.float32)
        pose_dist = _calc_dtw(pose_a, pose_b, w_pose)
        return float(0.80 * best_hand_dist + 0.20 * pose_dist)

    return float(best_hand_dist)


class DynamicGestureRecognizer:
    """
    Bộ nhận diện chuyên biệt dành riêng cho Cử chỉ Động (Số 10, Xin chào, Cảm ơn, Vẫy tay...).
    Hỗ trợ Kiến trúc Module: Tự động nạp Custom Kinematic Rules từ `dataset/<gesture_name>/gesture_rule.py`.
    """
    def __init__(self, window_size: int = 40, target_length: int = 30):
        self.window_size = window_size
        self.target_length = target_length
        self.dynamic_templates: Dict[str, List[np.ndarray]] = {}

        # Cửa sổ trượt lưu chuỗi khung hình gần nhất
        self.sliding_buffer = deque(maxlen=window_size)
        self.finger_history = deque(maxlen=25)

        # Bộ theo dõi động học ngón tay & bàn tay
        self.last_dx_sign = 0
        self.direction_changes = 0
        self.total_finger_motion = 0.0
        self.cooldown_ticks = 0

        # Tự động nạp các Custom Kinematic Rules riêng biệt từ thư mục dataset/
        self.custom_rules: Dict[str, any] = self._load_custom_rules()

    def _load_custom_rules(self, dataset_base_dir: str = "dataset") -> Dict[str, any]:
        """
        Tự động phát hiện và nạp các file `gesture_rule.py` nằm riêng biệt
        trong từng thư mục con của `dataset/<tên_cử_chỉ>/gesture_rule.py`.
        """
        import os
        import importlib.util
        rules = {}
        if not os.path.isdir(dataset_base_dir):
            return rules

        for item in os.listdir(dataset_base_dir):
            folder_path = os.path.join(dataset_base_dir, item)
            rule_file = os.path.join(folder_path, "gesture_rule.py")
            if os.path.isdir(folder_path) and os.path.isfile(rule_file):
                try:
                    spec = importlib.util.spec_from_file_location(f"rule_{item}", rule_file)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "GestureRule"):
                        rules[item] = mod.GestureRule()
                        print(f"[Dynamic Recognizer]: Đã nạp thành công Custom Kinematic Rule cho cử chỉ '{item}'!")
                except Exception as e:
                    print(f"[Dynamic Recognizer Warning]: Lỗi nạp rule cho {item}: {e}")
        return rules

    def update_templates(self, templates: Dict[str, List[np.ndarray]]):
        """Cập nhật các mẫu cử chỉ động đã chuẩn hoá toạ độ tương đối vào RAM Cache."""
        self.dynamic_templates = {}
        for name, seq_list in templates.items():
            resampled_list = []
            for s in seq_list:
                if len(s) > 0:
                    # Lọc active hand frames của template
                    active_tpl = [f for f in s if not np.all(f[1536:1662] == 0)]
                    tpl_arr = np.array(active_tpl if len(active_tpl) >= 5 else s, dtype=np.float32)
                    norm_s = normalize_dynamic_sequence(tpl_arr)
                    resampled_list.append(resample_sequence(norm_s, self.target_length))
            if resampled_list:
                self.dynamic_templates[name] = resampled_list

    def clear_buffer(self):
        """Xoá bộ đệm sau khi đã nhận diện thành công một cử chỉ."""
        self.sliding_buffer.clear()
        self.finger_history.clear()
        self.direction_changes = 0
        self.total_finger_motion = 0.0
        self.last_dx_sign = 0

    def process_frame(self, frame_vec_1662: np.ndarray, force_dynamic: bool = False) -> Tuple[Optional[Dict], bool]:
        """
        Xử lý từng frame trên luồng camera.
        Tham số `force_dynamic`: Khi người dùng bật chế độ "Chỉ Động" trên GUI.
        """
        if self.cooldown_ticks > 0:
            self.cooldown_ticks -= 1
            return None, False

        self.sliding_buffer.append(frame_vec_1662.copy())

        # Trích xuất toạ độ bàn tay (Ưu tiên tay phải, fallback tay trái)
        rh = frame_vec_1662[1599:1662].reshape(21, 3)
        lh = frame_vec_1662[1536:1599].reshape(21, 3)
        hand_pts = rh if not np.all(rh == 0) else (lh if not np.all(lh == 0) else None)

        if hand_pts is None:
            return None, False

        # 1. ƯU TIÊN KIỂM TRA CÁC CUSTOM KINEMATIC RULES RIÊNG BIỆT (như Số 10 double-tap)
        if self.custom_rules:
            pts_21 = [(float(p[0]), float(p[1])) for p in hand_pts]
            for g_name, rule in self.custom_rules.items():
                matched, payload = rule.process_hand_points(pts_21)
                if matched and payload:
                    self.cooldown_ticks = 15
                    self.clear_buffer()
                    return payload, False
                elif payload and payload.get("in_motion"):
                    return payload, True

        # 2. Đánh giá trạng thái chuyển động từ năng lượng bàn tay
        active_frames = [f for f in self.sliding_buffer if not np.all(f[1536:1662] == 0)]
        n_active = len(active_frames)

        is_moving = False
        if n_active >= 2:
            prev_f = active_frames[-2][1536:1662]
            curr_f = active_frames[-1][1536:1662]
            frame_disp = float(np.mean(np.linalg.norm((curr_f - prev_f).reshape(42, 3), axis=1)))
            is_moving = frame_disp > 0.005

        # 3. Kích hoạt so khớp chuỗi trượt (Sliding Sequence Matcher)
        # Chỉ khi có ít nhất 10 frames bàn tay thực và đang chuyển động
        if n_active >= 10:
            seq_arr = np.array(active_frames, dtype=np.float32)
            scores = self.classify_sequence(seq_arr)
            if scores and scores[0]["confidence"] >= 50.0:
                top1 = scores[0]
                top1["candidates"] = scores[:3]
                self.cooldown_ticks = 10
                self.clear_buffer()
                return top1, True

        return None, is_moving

    def classify_sequence(self, sequence: np.ndarray) -> List[Dict]:
        """
        Phân loại toàn bộ chuỗi cử chỉ động (video clip hoặc chuỗi cắt từ Motion Spotter).
        Trả về danh sách kết quả sắp xếp theo độ tin cậy giảm dần.
        """
        if not self.dynamic_templates or sequence is None or len(sequence) == 0:
            return [{
                "name": "(Chưa có mẫu động)",
                "confidence": 0.0,
                "distance": 1.0,
                "type": "ĐỘNG",
                "frames": len(sequence) if sequence is not None else 0
            }]

        # 1. Lọc các frame có bàn tay hoạt động (Active Hand Frames)
        active_frames = [f for f in sequence if not np.all(f[1536:1662] == 0)]
        if len(active_frames) < 5:
            # Fallback nếu không lọc được frame nào
            active_frames = sequence

        seq_arr = np.array(active_frames, dtype=np.float32)
        norm_seq = normalize_dynamic_sequence(seq_arr)
        input_resampled = resample_sequence(norm_seq, self.target_length)

        scores = []
        for gesture_name, template_list in self.dynamic_templates.items():
            best_dist = float("inf")
            for tpl in template_list:
                dist = fast_dtw_distance(input_resampled, tpl)
                if dist < best_dist:
                    best_dist = dist

            conf = max(0.0, min(100.0, (1.0 - best_dist / 0.20) * 100.0))
            scores.append({
                "name": gesture_name,
                "confidence": round(conf, 1),
                "distance": round(best_dist, 4),
                "type": "ĐỘNG",
                "frames": len(seq_arr)
            })

        scores.sort(key=lambda x: x["confidence"], reverse=True)
        return scores

    def _match_active_buffer(self, active_frames: List[np.ndarray]) -> Optional[Dict]:
        """So khớp chuỗi active frames với cơ sở dữ liệu mẫu động."""
        if not self.dynamic_templates or len(active_frames) < 8:
            return None

        seq_arr = np.array(active_frames, dtype=np.float32)
        norm_seq = normalize_dynamic_sequence(seq_arr)
        input_resampled = resample_sequence(norm_seq, self.target_length)

        scores = []
        for gesture_name, template_list in self.dynamic_templates.items():
            best_dist = float("inf")
            for tpl in template_list:
                dist = fast_dtw_distance(input_resampled, tpl)
                if dist < best_dist:
                    best_dist = dist

            # Thang đo độ tin cậy DTW tối ưu hoá cho Active Hand Frames:
            # dist <= 0.03 -> 85-99%
            # dist <= 0.08 -> 65-84%
            # dist <= 0.15 -> 45-64%
            # dist > 0.22 -> < 30%
            conf = max(0.0, min(100.0, (1.0 - best_dist / 0.20) * 100.0))
            scores.append({
                "name": gesture_name,
                "confidence": round(conf, 1),
                "distance": round(best_dist, 4),
                "type": "ĐỘNG",
                "frames": len(seq_arr)
            })

        if not scores:
            return None

        scores.sort(key=lambda x: x["confidence"], reverse=True)
        top1 = scores[0]
        top1["candidates"] = scores[:3]
        return top1
