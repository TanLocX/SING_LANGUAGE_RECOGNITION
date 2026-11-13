"""
TẦNG 1: GENERALIZED KINEMATIC SPOTTER (Bộ Phân Đoạn Chuỗi Động Học Tổng Quát)
=============================================================================
Module chịu trách nhiệm phân đoạn tự động (Temporal Gesture Spotting):
  1. Generalized Kinematic Energy:
     - Đo tổng năng lượng biến thiên vị trí của toàn bộ các khớp (Cổ tay, 5 đầu ngón tay, Cánh tay).
     - Không phụ thuộc vào bất kỳ ký tự hay cử chỉ cụ thể nào.
  2. Phân đoạn Chu kỳ Động tác (Onset - Apex - Offset):
     - IDLE: Tay đứng yên hoặc hạ xuống (Năng lượng < ngưỡng bắt đầu).
     - MOVING (Onset): Động năng tăng vọt khi tay bắt đầu chuyển động -> Tích lũy chuỗi cử chỉ.
     - COMPLETED (Offset): Động năng hạ thấp và ổn định liên tục -> Đóng gói chuỗi sạch [t_start -> t_end].
     - COOLDOWN: Nghỉ ngắn để chống trigger lặp lại.
"""

from collections import deque
import numpy as np
from typing import Optional, Tuple, Dict, List


class MotionState:
    IDLE = "IDLE"           # Tay nghỉ / hạ / đứng yên
    MOVING = "MOVING"       # Đang thực hiện cử chỉ động
    COMPLETED = "COMPLETED" # Vừa kết thúc chu kỳ động tác, sẵn sàng đưa vào phân loại
    COOLDOWN = "COOLDOWN"   # Tạm dừng ngắn tránh nhận diện lặp lại


class GeneralizedMotionSpotter:
    """
    Bộ phân đoạn động học tổng quát cho mọi cử chỉ động.
    """
    def __init__(
        self,
        energy_start_threshold: float = 0.012,   # Ngưỡng động năng kích hoạt Onset (Bắt đầu)
        energy_stop_threshold: float = 0.006,    # Ngưỡng động năng xác định Offset (Kết thúc)
        min_motion_frames: int = 12,             # Độ dài tối thiểu của một cử chỉ hợp lệ (frames)
        max_buffer_frames: int = 75,             # Độ dài tối đa của bộ đệm (~2.5 giây ở 30 FPS)
        settle_frames_needed: int = 4,           # Số frames ổn định liên tiếp để chốt kết thúc
        cooldown_ticks: int = 10,                # Số ticks tạm nghỉ sau khi chốt cử chỉ
        **kwargs
    ):
        if "velocity_start_threshold" in kwargs:
            energy_start_threshold = kwargs["velocity_start_threshold"]
        if "velocity_stop_threshold" in kwargs:
            energy_stop_threshold = kwargs["velocity_stop_threshold"]

        self.e_start = energy_start_threshold
        self.e_stop = energy_stop_threshold
        self.min_frames = min_motion_frames
        self.max_buffer = max_buffer_frames
        self.settle_needed = settle_frames_needed
        self.cooldown_ticks_max = cooldown_ticks

        self.state = MotionState.IDLE
        self.cooldown_counter = 0
        self.settle_counter = 0

        self.motion_buffer: List[np.ndarray] = []
        self.prev_keypoints: Optional[np.ndarray] = None
        self.recent_energies = deque(maxlen=6)

    def reset(self):
        """Đặt lại trạng thái bộ đệm về IDLE."""
        self.state = MotionState.IDLE
        self.cooldown_counter = 0
        self.settle_counter = 0
        self.motion_buffer.clear()
        self.recent_energies.clear()
        self.prev_keypoints = None

    def compute_frame_energy(self, current_vec_1662: np.ndarray) -> float:
        """
        Tính tổng động năng biến thiên (Kinematic Energy) trên toàn bộ các khớp quan trọng:
        - Bàn tay phải (1599:1662)
        - Bàn tay trái (1536:1599)
        - Cánh tay & Thân trên (0:132)
        """
        if self.prev_keypoints is None:
            self.prev_keypoints = current_vec_1662.copy()
            return 0.0

        energy = 0.0
        joint_count = 0

        # 1. Bàn tay phải
        rh_curr = current_vec_1662[1599:1662].reshape(21, 3)
        rh_prev = self.prev_keypoints[1599:1662].reshape(21, 3)
        if not np.all(rh_curr == 0) and not np.all(rh_prev == 0):
            d_rh = np.linalg.norm(rh_curr - rh_prev, axis=1)
            # Trọng số cao hơn cho các đầu ngón tay (Joints 4, 8, 12, 16, 20) và cổ tay (0)
            weights = np.ones(21, dtype=np.float32)
            weights[[0, 4, 8, 12, 16, 20]] = 2.0
            energy += float(np.average(d_rh, weights=weights))
            joint_count += 1

        # 2. Bàn tay trái
        lh_curr = current_vec_1662[1536:1599].reshape(21, 3)
        lh_prev = self.prev_keypoints[1536:1599].reshape(21, 3)
        if not np.all(lh_curr == 0) and not np.all(lh_prev == 0):
            d_lh = np.linalg.norm(lh_curr - lh_prev, axis=1)
            weights = np.ones(21, dtype=np.float32)
            weights[[0, 4, 8, 12, 16, 20]] = 2.0
            energy += float(np.average(d_lh, weights=weights))
            joint_count += 1

        # 3. Cánh tay (Pose thân trên: vai, khuỷu tay, cổ tay)
        pose_curr = current_vec_1662[0:132].reshape(33, 4)[:, :3]
        pose_prev = self.prev_keypoints[0:132].reshape(33, 4)[:, :3]
        if not np.all(pose_curr == 0) and not np.all(pose_prev == 0):
            # Khớp vai (11, 12), khuỷu tay (13, 14), cổ tay (15, 16)
            arm_idx = [11, 12, 13, 14, 15, 16]
            d_arms = np.linalg.norm(pose_curr[arm_idx] - pose_prev[arm_idx], axis=1)
            energy += float(np.mean(d_arms)) * 0.7
            joint_count += 1

        self.prev_keypoints = current_vec_1662.copy()
        return energy if joint_count > 0 else 0.0

    def process_frame(self, frame_vec_1662: np.ndarray) -> Tuple[str, Optional[np.ndarray], float]:
        """
        Xử lý từng frame từ camera stream:
        Trả về:
          - state: IDLE | MOVING | COMPLETED | COOLDOWN
          - completed_sequence: Mảng NumPy (T, 1662) khi kết thúc cử chỉ, ngược lại là None.
          - current_energy: Động năng chuyển động trung bình hiện tại.
        """
        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1
            if self.cooldown_counter == 0:
                self.state = MotionState.IDLE
            return MotionState.COOLDOWN, None, 0.0

        # Kiểm tra xem có bàn tay nào trong khung hình không
        has_hands = not np.all(frame_vec_1662[1536:1662] == 0)
        if not has_hands:
            if self.state == MotionState.MOVING and len(self.motion_buffer) >= self.min_frames:
                # Tay vừa hạ xuống ngoài khung hình sau khi hoàn thành cử chỉ
                completed_seq = np.array(self.motion_buffer, dtype=np.float32)
                self.reset()
                self.cooldown_counter = self.cooldown_ticks_max
                return MotionState.COMPLETED, completed_seq, 0.0
            self.reset()
            return MotionState.IDLE, None, 0.0

        instant_energy = self.compute_frame_energy(frame_vec_1662)
        self.recent_energies.append(instant_energy)
        smoothed_energy = float(np.mean(self.recent_energies))

        # ================= STATE MACHINE ĐỘNG HỌC =================

        if self.state == MotionState.IDLE:
            # Điều kiện Onset: Động năng vượt ngưỡng kích hoạt
            if smoothed_energy >= self.e_start:
                self.state = MotionState.MOVING
                self.settle_counter = 0
                self.motion_buffer = [frame_vec_1662.copy()]
                return MotionState.MOVING, None, smoothed_energy
            return MotionState.IDLE, None, smoothed_energy

        elif self.state == MotionState.MOVING:
            self.motion_buffer.append(frame_vec_1662.copy())

            # Giới hạn kích thước tối đa của bộ đệm
            if len(self.motion_buffer) > self.max_buffer:
                self.motion_buffer.pop(0)

            # Kiểm tra điều kiện Offset: Động năng giảm xuống dưới ngưỡng dừng
            if smoothed_energy <= self.e_stop:
                self.settle_counter += 1
            else:
                self.settle_counter = max(0, self.settle_counter - 1)

            # Khi động năng ổn định thấp liên tiếp đủ số frame quy định -> CHỐT CỬ CHỈ
            if self.settle_counter >= self.settle_needed and len(self.motion_buffer) >= self.min_frames:
                completed_seq = np.array(self.motion_buffer, dtype=np.float32)
                self.cooldown_counter = self.cooldown_ticks_max
                self.state = MotionState.COOLDOWN
                self.motion_buffer.clear()
                self.settle_counter = 0
                return MotionState.COMPLETED, completed_seq, smoothed_energy

            return MotionState.MOVING, None, smoothed_energy

        return MotionState.IDLE, None, 0.0


# Giữ alias KinematicMotionSpotter để tương thích 100% với code hiện có
KinematicMotionSpotter = GeneralizedMotionSpotter
