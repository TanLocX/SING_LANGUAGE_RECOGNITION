"""
Static Gesture Recognition Module (Mô-đun Độc Lập Chuyên Xử Lý Cử Chỉ Tĩnh)
=============================================================================
Được tách riêng hoàn toàn từ hệ thống chính để độc lập hóa bài toán Single-Frame Hand Shape.

Đảm nhiệm:
  - Chuẩn hoá hình thái học 21 khớp bàn tay (Hand Shape Alignment).
  - Khử tịnh tiến (Translation Invariant): Dời cổ tay về gốc (0, 0, 0).
  - Chuẩn hoá tỉ lệ (Scale Invariant): Chuẩn theo khoảng cách cổ tay -> ngón giữa.
  - Khử góc xoay (Rotation Invariant): Tự động xoay bàn tay thẳng đứng (-Y).
  - So khớp đối xứng hai tay (Mirror-X Invariant): Dùng tốt cho cả tay Trái và Phải.
  - Tự động nạp dữ liệu từ thư mục `dataset_static`.
"""

import os
import glob
import numpy as np
from typing import Dict, List, Optional, Tuple


def align_hand_landmarks(hand_coords_21x3: np.ndarray) -> np.ndarray:
    """
    Chuẩn hoá hình thái học bàn tay 21 điểm (shape: 21, 3):
      1. Tịnh tiến gốc toạ độ về cổ tay (wrist = index 0).
      2. Chuẩn hoá tỉ lệ (scale) theo độ dài xương bàn tay (wrist -> middle finger MCP = index 9).
      3. Khử góc xoay (Rotation Alignment): xoay vector cổ tay -> ngón giữa về hướng thẳng đứng (0, -1).
    """
    if hand_coords_21x3 is None or len(hand_coords_21x3) != 21:
        return np.zeros((21, 3), dtype=np.float32)

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
    # Trong MediaPipe, trục -Y là hướng LÊN TRÊN. Ta xoay vector v về góc -pi/2
    current_angle = float(np.arctan2(v[1], v[0]))
    target_angle = -np.pi / 2.0
    diff_angle = target_angle - current_angle

    cos_a, sin_a = float(np.cos(diff_angle)), float(np.sin(diff_angle))
    R = np.array([[cos_a, -sin_a], [sin_a, cos_a]], dtype=np.float32)

    aligned = scaled.copy().astype(np.float32)
    aligned[:, :2] = np.dot(scaled[:, :2], R.T)
    return aligned


def extract_hand_shape_from_sequence(seq_Nx1662: np.ndarray) -> Optional[np.ndarray]:
    """
    Trích xuất hình thái bàn tay chuẩn hóa từ chuỗi keypoints 1662 điểm:
    - Bàn tay phải: 1599:1662
    - Bàn tay trái: 1536:1599
    Lấy trung vị (median) của các frame có bàn tay xuất hiện để tạo template tĩnh sạch nhất.
    """
    if seq_Nx1662 is None or len(seq_Nx1662) == 0:
        return None

    rh_shapes = []
    lh_shapes = []
    for f in seq_Nx1662:
        rh = f[1599:1662].reshape(21, 3)
        if not np.all(rh == 0):
            rh_shapes.append(align_hand_landmarks(rh))

        lh = f[1536:1599].reshape(21, 3)
        if not np.all(lh == 0):
            lh_shapes.append(align_hand_landmarks(lh))

    if len(rh_shapes) >= len(lh_shapes) and len(rh_shapes) > 0:
        return np.median(np.array(rh_shapes), axis=0)
    elif len(lh_shapes) > 0:
        return np.median(np.array(lh_shapes), axis=0)

    return None


class StaticGestureRecognizer:
    """
    Bộ nhận diện chuyên biệt dành riêng cho Cử chỉ Tĩnh (Chữ cái A, B, C, D... và số tĩnh).
    """
    def __init__(self, dataset_dir: str = None):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        default_dir = os.path.join(root_dir, "DATA", "static", "dataset_static")
        self.dataset_dir = dataset_dir or (default_dir if os.path.isdir(default_dir) else os.path.join(os.path.dirname(__file__), "dataset_static"))
        self.static_templates: Dict[str, List[np.ndarray]] = {}
        self.load_dataset(self.dataset_dir)

    def load_dataset(self, dataset_dir: str):
        """Nạp toàn bộ mẫu tĩnh từ thư mục dataset_static và dataset.npz."""
        self.static_templates = {}
        if os.path.isdir(dataset_dir):
            for root, dirs, files in os.walk(dataset_dir):
                for f in files:
                    if f.endswith(".npy"):
                        full_path = os.path.join(root, f)
                        label = os.path.basename(root)
                        if label == os.path.basename(dataset_dir):
                            label = f.split("_")[0]
                        try:
                            arr = np.load(full_path)
                            if arr.ndim == 2 and arr.shape[1] == 1662:
                                h_shape = extract_hand_shape_from_sequence(arr)
                                if h_shape is not None:
                                    self.static_templates.setdefault(label, []).append(h_shape)
                            elif arr.ndim == 2 and arr.shape == (21, 3):
                                norm_h = align_hand_landmarks(arr)
                                self.static_templates.setdefault(label, []).append(norm_h)
                        except Exception as e:
                            print(f"[Static Loader Warning]: Lỗi đọc {full_path}: {e}")

        # Nạp dataset.npz nếu có (ưu tiên tìm trong DATA/static/dataset.npz)
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        npz_candidates = [
            os.path.join(root_dir, "DATA", "static", "dataset.npz"),
            os.path.join(os.path.dirname(__file__), "dataset.npz"),
            "DATA/static/dataset.npz",
            "dataset.npz"
        ]
        for npz_file in npz_candidates:
            if os.path.isfile(npz_file):
                try:
                    npz_data = np.load(npz_file, allow_pickle=True)
                    if 'X' in npz_data and 'labels' in npz_data:
                        X_arr = npz_data['X']
                        labels_arr = npz_data['labels']
                        for idx, x_sample in enumerate(X_arr):
                            lbl = str(labels_arr[idx]).strip()
                            h_shape = extract_hand_shape_from_sequence(x_sample)
                            if h_shape is not None:
                                self.static_templates.setdefault(lbl, []).append(h_shape)
                        break
                except Exception as e:
                    print(f"[Static Loader Warning]: Lỗi đọc dataset.npz ({npz_file}): {e}")

        print(f"[StaticGestureRecognizer]: Đã nạp thành công {len(self.static_templates)} nhãn tĩnh: {list(self.static_templates.keys())}")

    def update_templates(self, templates: Dict[str, List[np.ndarray]]):
        """Cập nhật cơ sở dữ liệu mẫu cử chỉ tĩnh vào RAM Cache."""
        self.static_templates = templates or {}

    def recognize_frame(self, hand_landmarks) -> Optional[Dict]:
        """
        Nhận diện ký tự tĩnh từ 1 frame đơn lẻ.
        hand_landmarks có thể là MediaPipe landmark object hoặc mảng numpy (21, 3).
        """
        if not hand_landmarks or not self.static_templates:
            return None

        # Trích xuất toạ độ 21 điểm bàn tay
        if hasattr(hand_landmarks, "landmark"):
            pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)
        else:
            pts = np.array(hand_landmarks, dtype=np.float32).reshape(21, 3)

        if np.all(pts == 0):
            return None

        norm_hand = align_hand_landmarks(pts)

        # Bản lật ngang (Mirror X) để nhận diện bất biến cả tay Trái và Phải
        norm_hand_flipped = norm_hand.copy()
        norm_hand_flipped[:, 0] = -norm_hand_flipped[:, 0]
        norm_hand_flipped = align_hand_landmarks(norm_hand_flipped)

        weights = np.array([1.0, 1.0, 0.4], dtype=np.float32)
        scores = []

        for gesture_name, shapes_list in self.static_templates.items():
            best_g_dist = float("inf")
            for tpl_shape in shapes_list:
                # 1. So khớp trực tiếp
                d_dir = float(np.mean(np.linalg.norm((norm_hand - tpl_shape) * weights, axis=1)))
                # 2. So khớp lật đối xứng (cho phép dùng cả tay Trái hoặc Phải)
                d_flip = float(np.mean(np.linalg.norm((norm_hand_flipped - tpl_shape) * weights, axis=1)))

                cur_min = min(d_dir, d_flip)
                if cur_min < best_g_dist:
                    best_g_dist = cur_min

            # Thang đo độ tin cậy mượt mà:
            # Sai số <= 0.05 -> 86-98%
            # Sai số <= 0.15 -> 64-85%
            # Sai số <= 0.25 -> 47-63%
            conf = max(0.0, min(100.0, 100.0 * float(np.exp(-3.0 * best_g_dist))))
            scores.append({
                "name": gesture_name,
                "confidence": round(conf, 1),
                "distance": round(best_g_dist, 3),
                "type": "TĨNH"
            })

        if not scores:
            return None

        scores.sort(key=lambda x: x["confidence"], reverse=True)
        top1 = scores[0]
        top1["candidates"] = scores[:3]
        return top1

