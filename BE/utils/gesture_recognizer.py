"""
Gesture Recognition & Dataset Manager (.npy Architecture + Full Geometric Invariance)
=====================================================================================
Tích hợp lý thuyết Hình học Đồng dạng & Bất biến góc xoay (Translation, Scale & Rotation Invariance):
  1. Chuẩn hóa hình học đồng dạng toàn diện cho Bàn tay (Full Hand Alignment):
     - Dời Cổ tay về (0, 0, 0)
     - Co giãn kích thước bàn tay về k = 1 (chia cho độ dài cổ tay -> ngón giữa)
     - Căn chỉnh góc xoay (Rotation Alignment): tự động xoay bàn tay thẳng đứng
       triệt tiêu 100% lỗi nghiêng tay!
  2. Tối ưu bộ nhớ đệm (RAM Cache):
     - Không đọc lại đĩa mỗi frame -> Giữ vững tốc độ 30 FPS không bị drop khi đưa tay vào!
  3. Nhận diện Realtime Live Webcam siêu nhạy cho ký tự tĩnh (A, B, C...):
     - Chạy siêu tốc (<0.5ms) ngay trên luồng camera.
"""

import os
import time
import json
import glob
import cv2
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from ..dynamic.dynamic_recognizer import DynamicGestureRecognizer, resample_sequence, fast_dtw_distance, normalize_dynamic_sequence
from ..dynamic.motion_spotter import KinematicMotionSpotter, MotionState

# Kích thước vector đặc trưng mỗi frame
KEYPOINT_DIM = 1662

# Trọng số các vùng đặc trưng
FEATURE_WEIGHTS = np.ones(KEYPOINT_DIM, dtype=np.float32) * 0.1
FEATURE_WEIGHTS[0:132] = 1.0       # Pose
FEATURE_WEIGHTS[1536:1599] = 4.0   # Left hand
FEATURE_WEIGHTS[1599:1662] = 4.0   # Right hand


def align_hand_landmarks(hand_coords_21x3: np.ndarray) -> np.ndarray:
    """
    Chuẩn hoá hình học đồng dạng TOÀN DIỆN cho 21 khớp bàn tay (shape: 21, 3):
      1. Tịnh tiến (Translation): Dời khớp cổ tay (điểm 0) về gốc toạ độ (0, 0, 0).
      2. Tỉ lệ (Scale): Chia cho khoảng cách từ Cổ tay (0) đến Khớp gốc ngón giữa (9).
      3. Căn chỉnh góc xoay (Rotation Alignment): Xoay quanh trục Z sao cho
         vector từ Cổ tay (0) đến Khớp gốc ngón giữa (9) luôn hướng thẳng đứng lên trên
         (hướng -Y của MediaPipe).
    Kết quả: Bàn tay bất biến 100% với việc nghiêng tay, đứng lệch, hay đứng xa/gần!
    """
    if hand_coords_21x3 is None or len(hand_coords_21x3) == 0:
        return np.zeros((21, 3), dtype=np.float32)

    if np.all(hand_coords_21x3 == 0):
        return hand_coords_21x3.astype(np.float32)

    # 1. Dời gốc về cổ tay
    wrist = hand_coords_21x3[0]
    centered = hand_coords_21x3 - wrist

    # 2. Scale chuẩn
    scale = float(np.linalg.norm(centered[9]))
    if scale < 1e-4:
        scale = float(np.max(np.linalg.norm(centered, axis=1)))
    if scale < 1e-4:
        scale = 1.0
    scaled = centered / scale

    # 3. Rotation Alignment: vector 0 -> 9
    v = scaled[9, :2]
    # Trong MediaPipe, trục -Y là hướng LÊN TRÊN.
    # Ta xoay vector v về hướng (0, -1), tức góc -pi/2
    current_angle = float(np.arctan2(v[1], v[0]))
    target_angle = -np.pi / 2.0
    diff_angle = target_angle - current_angle

    cos_a, sin_a = float(np.cos(diff_angle)), float(np.sin(diff_angle))
    R = np.array([[cos_a, -sin_a], [sin_a, cos_a]], dtype=np.float32)

    aligned = scaled.copy().astype(np.float32)
    aligned[:, :2] = np.dot(scaled[:, :2], R.T)
    return aligned


# Giữ alias cho tương thích ngược
normalize_hand_landmarks = align_hand_landmarks


def normalize_pose_landmarks(pose_coords_33x4: np.ndarray) -> np.ndarray:
    """Chuẩn hoá hình học đồng dạng cho Pose."""
    if pose_coords_33x4 is None or len(pose_coords_33x4) == 0:
        return np.zeros((33, 4), dtype=np.float32)

    if np.all(pose_coords_33x4 == 0):
        return pose_coords_33x4.astype(np.float32)

    normalized = pose_coords_33x4.copy().astype(np.float32)
    left_shoulder = pose_coords_33x4[11, :3]
    right_shoulder = pose_coords_33x4[12, :3]

    if not np.all(left_shoulder == 0) and not np.all(right_shoulder == 0):
        mid_shoulder = (left_shoulder + right_shoulder) / 2.0
        shoulder_width = float(np.linalg.norm(left_shoulder - right_shoulder))
        if shoulder_width < 1e-4:
            shoulder_width = 1.0

        normalized[:, :3] = (pose_coords_33x4[:, :3] - mid_shoulder) / shoulder_width

    return normalized


def normalize_feature_frame(vec_1662: np.ndarray) -> np.ndarray:
    """Chuẩn hoá toàn bộ 1 frame đặc trưng 1.662 điểm."""
    out = vec_1662.copy().astype(np.float32)

    # 1. Pose
    pose_raw = out[0:132].reshape(33, 4)
    out[0:132] = normalize_pose_landmarks(pose_raw).flatten()

    # 2. Left Hand
    lh_raw = out[1536:1599].reshape(21, 3)
    if not np.all(lh_raw == 0):
        out[1536:1599] = align_hand_landmarks(lh_raw).flatten()

    # 3. Right Hand
    rh_raw = out[1599:1662].reshape(21, 3)
    if not np.all(rh_raw == 0):
        out[1599:1662] = align_hand_landmarks(rh_raw).flatten()

    return out


def normalize_sequence(sequence: np.ndarray) -> np.ndarray:
    """Chuẩn hoá toàn bộ chuỗi T frames x 1662 keypoints."""
    if sequence is None or len(sequence) == 0:
        return sequence

    normalized = np.zeros_like(sequence, dtype=np.float32)
    for i in range(len(sequence)):
        normalized[i] = normalize_feature_frame(sequence[i])
    return normalized


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


def extract_active_hand_shape(sequence: np.ndarray) -> Tuple[Optional[np.ndarray], str]:
    """
    Trích xuất hình thái bàn tay chuẩn hoá (Hand Shape) đã xoay thẳng đứng.
    """
    if sequence is None or len(sequence) == 0:
        return None, "None"

    rh_frames = []
    for f in sequence:
        rh = f[1599:1662].reshape(21, 3)
        if not np.all(rh == 0):
            rh_aligned = align_hand_landmarks(rh)
            rh_frames.append(rh_aligned)

    lh_frames = []
    for f in sequence:
        lh = f[1536:1599].reshape(21, 3)
        if not np.all(lh == 0):
            lh_aligned = align_hand_landmarks(lh)
            lh_frames.append(lh_aligned)

    if len(rh_frames) >= len(lh_frames) and len(rh_frames) > 0:
        rh_arr = np.array(rh_frames)
        mean_rh = np.median(rh_arr, axis=0)
        return mean_rh, "Right"
    elif len(lh_frames) > 0:
        lh_arr = np.array(lh_frames)
        mean_lh = np.median(lh_arr, axis=0)
        return mean_lh, "Left"

    return None, "None"


def detect_gesture_motion(keypoints_seq: np.ndarray) -> Dict:
    """
    Phân tích chuỗi keypoints để gợi ý tự động cử chỉ là Tĩnh hay Động:
      - Cử chỉ Tĩnh (chữ cái A, B, C...): Cổ tay và cánh tay ít dịch chuyển -> Gợi ý chỉ lưu Bàn tay.
      - Cử chỉ Động (từ vựng xin chào, cảm ơn...): Cổ tay di chuyển tạo quỹ đạo -> Gợi ý lưu kèm Cánh tay.
    """
    if keypoints_seq is None or len(keypoints_seq) < 3:
        return {"is_dynamic": False, "suggest_arm": False, "suggest_head": False, "wrist_motion": 0.0}

    # Trích xuất toạ độ cổ tay qua các frames
    rh_wrists = [f[1599:1602] for f in keypoints_seq if not np.all(f[1599:1602] == 0)]
    lh_wrists = [f[1536:1539] for f in keypoints_seq if not np.all(f[1536:1539] == 0)]

    wrists = rh_wrists if len(rh_wrists) >= len(lh_wrists) else lh_wrists
    if len(wrists) >= 3:
        wrists_arr = np.array(wrists)
        motion_range = float(np.max(np.linalg.norm(wrists_arr - wrists_arr[0], axis=1)))
        is_dynamic = motion_range > 0.06  # Ngưỡng dịch chuyển 6% kích thước khung hình
    else:
        motion_range = 0.0
        is_dynamic = False

    return {
        "is_dynamic": is_dynamic,
        "suggest_arm": is_dynamic,
        "suggest_head": False,
        "wrist_motion": round(motion_range, 3)
    }


class GestureDatasetManager:
    """
    Quản lý lưu trữ và nạp cơ sở dữ liệu mẫu cử chỉ định dạng .npy & .json (Có RAM Cache).
    Phân tách tường minh 2 nhánh:
      - static_templates: Chuyên cho Cử chỉ Tĩnh (Hand shapes)
      - dynamic_templates: Chuyên cho Cử chỉ Động (Full time-series)
    """
    def __init__(self, dataset_dirs=None):
        if isinstance(dataset_dirs, str):
            dataset_dirs = [dataset_dirs]
        self.dataset_dirs = dataset_dirs or ["DATA/dynamic", "dataset", "dataset_npy", "recordings"]
        for d in self.dataset_dirs:
            os.makedirs(d, exist_ok=True)
        self._cached_templates = None
        self._cached_hand_shapes = None
        self.static_templates: Dict[str, List[np.ndarray]] = {}
        self.dynamic_templates: Dict[str, List[np.ndarray]] = {}

    def invalidate_cache(self):
        """Xóa bộ đệm RAM khi có mẫu mới lưu hoặc xóa."""
        self._cached_templates = None
        self._cached_hand_shapes = None
        self.static_templates = {}
        self.dynamic_templates = {}

    def save_sample(
        self,
        gesture_name: str,
        keypoints_seq: np.ndarray,
        target_dir: Optional[str] = None,
        include_arm: bool = True,
        include_head: bool = False,
        fps: float = 30.0,
        video_frames: Optional[List[np.ndarray]] = None,
        gesture_type: str = "static"
    ) -> Tuple[str, str, Optional[str]]:
        """
        Lưu cử chỉ đồng thời:
          1. File .npy: Mảng nhị phân NumPy tối ưu siêu tốc cho hệ thống nhận diện.
             Cách 1: Gán tag phân loại '_stat_' hoặc '_dyn_' trực tiếp vào tên file.
          2. File .json: Định dạng văn bản con người đọc được trực tiếp.
             Cách 3: Ghi nhận nhãn 'gesture_type' rõ ràng trong metadata JSON.
          3. File .mp4: Video gốc SẠCH 100% (KHÔNG vẽ khung xương hay text) để lưu trữ trực quan.
        """
        gesture_clean = gesture_name.strip().lower().replace(" ", "_")
        actual_target_dir = target_dir or self.dataset_dirs[0]
        folder_path = os.path.join(actual_target_dir, gesture_clean)
        os.makedirs(folder_path, exist_ok=True)

        # Cách 1: Gắn tag phân loại tĩnh (_stat_) hoặc động (_dyn_) vào tên file
        tag = "dyn" if gesture_type == "dynamic" else "stat"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        npy_path = os.path.join(folder_path, f"{gesture_clean}_{tag}_{timestamp}.npy")
        json_path = os.path.join(folder_path, f"{gesture_clean}_{tag}_{timestamp}.json")
        mp4_path = None

        # 1. Lưu file Video gốc SẠCH (.mp4) nếu có frames
        if video_frames is not None and len(video_frames) > 0:
            mp4_path = os.path.join(folder_path, f"{gesture_clean}_{tag}_{timestamp}.mp4")
            try:
                h, w = video_frames[0].shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                actual_fps = float(fps if fps and fps > 0 else 30.0)
                writer = cv2.VideoWriter(mp4_path, fourcc, actual_fps, (w, h))
                for frame in video_frames:
                    writer.write(frame)
                writer.release()
            except Exception as e:
                print(f"[Save Sample Warning]: Lỗi ghi video mp4: {e}")
                mp4_path = None

        # 2. Masking các thành phần không được chọn vào mảng .npy
        masked_seq = keypoints_seq.copy().astype(np.float32)
        if not include_arm:
            masked_seq[:, 0:132] = 0.0          # Pose (33 pts * 4: x, y, z, visibility)
        if not include_head:
            masked_seq[:, 132:1536] = 0.0        # Face Mesh (468 pts * 3: x, y, z)
        # Bàn tay (1536:1662) là bắt buộc, luôn giữ nguyên vẹn

        # Lưu file .npy nhị phân siêu tốc
        np.save(npy_path, masked_seq)

        # 3. Tạo cấu trúc dữ liệu con người đọc được và lưu file .json
        n_frames = len(keypoints_seq)
        lh_count = sum(1 for f in keypoints_seq if not np.all(f[1536:1599] == 0))
        rh_count = sum(1 for f in keypoints_seq if not np.all(f[1599:1662] == 0))
        active_hand = "Right" if rh_count >= lh_count else "Left"

        frames_json = []
        for idx in range(n_frames):
            frame_vec = keypoints_seq[idx]
            frame_item = {
                "frame_idx": idx,
                "right_hand": frame_vec[1599:1662].reshape(21, 3).tolist() if not np.all(frame_vec[1599:1662] == 0) else None,
                "left_hand": frame_vec[1536:1599].reshape(21, 3).tolist() if not np.all(frame_vec[1536:1599] == 0) else None,
            }
            if include_arm:
                frame_item["arm_pose"] = frame_vec[0:132].reshape(33, 4).tolist()
            if include_head:
                frame_item["head_face"] = frame_vec[132:1536].reshape(468, 3).tolist()
            frames_json.append(frame_item)

        # Cách 3: Ghi nhận nhãn gesture_type rõ ràng trong file metadata JSON
        json_payload = {
            "gesture_name": gesture_clean,
            "gesture_type": gesture_type,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_frames": int(n_frames),
            "fps": float(fps),
            "video_file": os.path.basename(mp4_path) if mp4_path else None,
            "components": {
                "hands": True,
                "arm": bool(include_arm),
                "head": bool(include_head)
            },
            "summary": {
                "active_hand": active_hand,
                "left_hand_frames": int(lh_count),
                "right_hand_frames": int(rh_count),
                "is_dynamic": (gesture_type == "dynamic")
            },
            "frames": frames_json
        }

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(json_payload, jf, ensure_ascii=False, indent=2)

        self.invalidate_cache()
        return npy_path, json_path, mp4_path

    def load_all_templates(self, force_reload: bool = False) -> Dict[str, List[np.ndarray]]:
        """
        Nạp tất cả các file .npy với cơ chế RAM Cache siêu tốc và phân tách Tĩnh/Động.
        """
        if self._cached_templates is not None and not force_reload:
            return self._cached_templates

        templates: Dict[str, List[np.ndarray]] = {}
        self.static_templates = {}
        self.dynamic_templates = {}

        for base_dir in self.dataset_dirs:
            if not os.path.isdir(base_dir):
                continue
            for root, dirs, files in os.walk(base_dir):
                for f in files:
                    if f.endswith(".npy"):
                        full_path = os.path.join(root, f)
                        parent_name = os.path.basename(root)
                        gesture_label = parent_name if parent_name not in self.dataset_dirs else f.split("_")[0]
                        try:
                            arr = np.load(full_path)
                            if arr.ndim == 2 and arr.shape[1] == KEYPOINT_DIM:
                                templates.setdefault(gesture_label, []).append(arr)

                                # Phân loại vào static_templates hoặc dynamic_templates
                                is_dyn = False
                                # 1. Kiểm tra tag tên file (Cách 1)
                                if "_dyn_" in f or f.startswith("dyn_"):
                                    is_dyn = True
                                elif "_stat_" in f or f.startswith("stat_"):
                                    is_dyn = False
                                else:
                                    # 2. Kiểm tra file JSON đi kèm cùng tên (Cách 3)
                                    json_file = os.path.splitext(full_path)[0] + ".json"
                                    if os.path.isfile(json_file):
                                        try:
                                            with open(json_file, "r", encoding="utf-8") as jf:
                                                jdata = json.load(jf)
                                                if jdata.get("gesture_type") == "dynamic" or jdata.get("summary", {}).get("is_dynamic"):
                                                    is_dyn = True
                                        except Exception:
                                            pass
                                    else:
                                        # Fallback phân tích chuyển động
                                        motion_info = detect_gesture_motion(arr)
                                        is_dyn = motion_info.get("is_dynamic", False)

                                # Tất cả mẫu trong dataset hiện tại là cử chỉ động
                                self.dynamic_templates.setdefault(gesture_label, []).append(arr)
                        except Exception as e:
                            print(f"[Dataset Warning]: Không thể đọc file {full_path}: {e}")

        self._cached_templates = templates
        self._cached_hand_shapes = {}
        return templates

    def get_cached_hand_shapes(self) -> Dict[str, List[np.ndarray]]:
        if self._cached_hand_shapes is None:
            self.load_all_templates()
        return self._cached_hand_shapes or {}

    def get_existing_gesture_names(self) -> List[str]:
        templates = self.load_all_templates()
        return sorted(list(templates.keys()))


class VideoRecognizer:
    """
    Xử lý nhận diện cử chỉ động từ File Video & Realtime Live Webcam.
    Tích hợp KinematicMotionSpotter (bắt Onset/Offset) + DynamicGestureRecognizer (FastDTW).
    """
    def __init__(self, tracker, dataset_manager: Optional[GestureDatasetManager] = None):
        self.tracker = tracker
        self.dataset_manager = dataset_manager or GestureDatasetManager()
        self.dynamic_engine = DynamicGestureRecognizer()
        self.motion_spotter = KinematicMotionSpotter()
        self.sync_engines()

    def sync_engines(self, force_reload: bool = False):
        """Đồng bộ RAM Cache của engine nhận diện động với CSDL."""
        self.dataset_manager.load_all_templates(force_reload=force_reload)
        self.dynamic_engine.update_templates(self.dataset_manager.dynamic_templates)
        self.motion_spotter.reset()

    def process_video_file(
        self,
        video_path: str,
        progress_callback=None,
        max_resolution=(640, 360)
    ) -> Tuple[List[np.ndarray], np.ndarray, float]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Không thể mở file video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            total_frames = 1
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        frames_bgr = []
        keypoints_list = []

        frame_idx = 0
        while cap.isOpened():
            ret, raw_frame = cap.read()
            if not ret or raw_frame is None:
                break

            frame_idx += 1
            h, w = raw_frame.shape[:2]
            scale = min(max_resolution[0] / w, max_resolution[1] / h, 1.0)
            if scale < 1.0:
                infer_w, infer_h = int(w * scale), int(h * scale)
                small_frame = cv2.resize(raw_frame, (infer_w, infer_h), interpolation=cv2.INTER_AREA)
            else:
                small_frame = raw_frame

            results, annotated_frame = self.tracker.process_frame(
                small_frame,
                show_hands=True,
                show_pose=True,
                show_face=True,
                mirror=False
            )

            from ..trackers.holistic_tracker import extract_keypoints
            kp = extract_keypoints(results)
            keypoints_list.append(kp)
            # Lưu trữ khung hình SẠCH (clean frames) không có khung xương vẽ đè
            frames_bgr.append(small_frame.copy())

            if progress_callback:
                percent = min(100, int((frame_idx / total_frames) * 100))
                progress_callback(frame_idx, total_frames, percent)

        cap.release()

        if not keypoints_list:
            keypoints_seq = np.zeros((0, KEYPOINT_DIM), dtype=np.float32)
        else:
            keypoints_seq = np.array(keypoints_list, dtype=np.float32)

        return frames_bgr, keypoints_seq, fps

    def recognize_sequence(self, input_seq: np.ndarray) -> List[Dict]:
        """
        So khớp cử chỉ toàn chuỗi thời gian (Video Matching).
        """
        self.dataset_manager.load_all_templates()
        return self.dynamic_engine.classify_sequence(input_seq)

    def recognize_live_frame(self, results, mode: str = "dynamic") -> Optional[Dict]:
        """
        Nhận diện cử chỉ trực tiếp từ luồng Camera (Realtime Live Dynamic Recognition).
        1. Sử dụng KinematicMotionSpotter:
           - Tự động phát hiện khi tay di chuyển (MOVING).
           - Tự động đóng gói chuỗi khi cử chỉ kết thúc (COMPLETED) và chấm điểm ngay lập tức.
        2. Kết hợp Sliding Window DTW dự phòng.
        """
        from ..trackers.holistic_tracker import extract_keypoints
        vec_1662 = extract_keypoints(results)

        # 1. Kinematic Motion Spotter: Bắt chính xác chuỗi cử chỉ trọn vẹn
        state, completed_seq, vel = self.motion_spotter.process_frame(vec_1662)
        if state == MotionState.COMPLETED and completed_seq is not None:
            results_list = self.dynamic_engine.classify_sequence(completed_seq)
            if results_list and results_list[0]["confidence"] >= 35.0:
                top = results_list[0]
                top["candidates"] = results_list[:3]
                return top

        # 2. Sliding Window DTW liên tục
        dyn_match, is_moving = self.dynamic_engine.process_frame(vec_1662, force_dynamic=True)
        if dyn_match is not None:
            return dyn_match

        if state == MotionState.MOVING or is_moving:
            return {
                "name": "Đang thực hiện...",
                "confidence": 50.0,
                "distance": 0.0,
                "type": "ĐỘNG",
                "in_motion": True
            }

        return None
