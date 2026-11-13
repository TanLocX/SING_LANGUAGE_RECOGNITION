"""
Gesture Kinematic Rule: Ký hiệu Số 10 (Double-Tap Pinch Detector)
================================================================
Thư mục: dataset/10/gesture_rule.py
Áp dụng giải thuật từ REPO/morse/test.py:
  1. Hand Scale Normalization: Chuẩn hoá khoảng cách theo tỷ lệ lòng bàn tay
  2. Hysteresis State Machine: 2 ngưỡng (Pinch <= 0.22, Release >= 0.32)
  3. Chu kỳ chạm kép: Bắt buộc chạm ngón cái và ngón trỏ đúng 2 lần liên tiếp.
     - Giữ nguyên tay chạm nhau: Bị chặn (không tính lần 2).
     - Mới chạm 1 lần: Báo trạng thái đang làm (không kích hoạt sớm).
     - Chạm đủ 2 lần: Kích hoạt Số 10.
"""

import math
import time
from typing import Dict, Optional, Tuple, List
import numpy as np


class GestureRule:
    """
    Quy tắc động học riêng biệt cho cử chỉ Số 10.
    """
    def __init__(
        self,
        pinch_threshold: float = 0.22,     # Ngưỡng khoảng cách khi 2 ngón CHẠM nhau
        release_threshold: float = 0.32,   # Ngưỡng khoảng cách khi 2 ngón MỞ RA
        max_tap_interval: float = 1.6,     # Thời gian tối đa cho phép giữa 2 lần chạm (giây)
        cooldown_duration: float = 1.0     # Thời gian tạm nghỉ sau khi nhận diện thành công (giây)
    ):
        self.gesture_name = "10"
        self.pinch_thresh = pinch_threshold
        self.release_thresh = release_threshold
        self.max_interval = max_tap_interval
        self.cooldown_duration = cooldown_duration

        # Biến trạng thái
        self.tap_count = 0
        self.is_pinched = False
        self.last_tap_time = 0.0
        self.last_success_time = 0.0

    def reset(self):
        """Đặt lại toàn bộ trạng thái về ban đầu."""
        self.tap_count = 0
        self.is_pinched = False
        self.last_tap_time = 0.0

    def process_hand_points(self, pts_21: List[Tuple[float, float]]) -> Tuple[bool, Optional[Dict]]:
        """
        Xử lý tọa độ 21 điểm của bàn tay (dạng normalized hoặc pixel).
        Trả về:
          - is_matched (bool): True nếu đã hoàn thành đúng 2 lần chạm số 10.
          - result_payload (dict hoặc None): Dữ liệu kết quả cử chỉ hoặc trạng thái in_motion.
        """
        now = time.time()

        # Kiểm tra cooldown sau khi vừa nhận diện thành công
        if (now - self.last_success_time) < self.cooldown_duration:
            return False, None

        # Reset bộ đếm nếu quá lâu không thực hiện cú chạm thứ 2
        if self.tap_count > 0 and (now - self.last_tap_time) > self.max_interval:
            self.reset()

        if pts_21 is None or len(pts_21) < 21:
            self.reset()
            return False, None

        # 1. Tính thước đo lòng bàn tay (Hand Scale) chuẩn hoá từ test.py
        wrist = pts_21[0]
        mid_mcp = pts_21[9]
        idx_mcp = pts_21[5]
        pnk_mcp = pts_21[17]

        palm_len = math.hypot(wrist[0] - mid_mcp[0], wrist[1] - mid_mcp[1])
        palm_wid = math.hypot(idx_mcp[0] - pnk_mcp[0], idx_mcp[1] - pnk_mcp[1])
        hand_scale = max(0.01, (palm_len + palm_wid) * 0.55)

        # 2. Khoảng cách chuẩn hoá giữa đầu ngón cái (4) và đầu ngón trỏ (8)
        thumb = pts_21[4]
        index = pts_21[8]
        dist_ratio = math.hypot(thumb[0] - index[0], thumb[1] - index[1]) / hand_scale

        # 3. Máy trạng thái trễ 2 ngưỡng (Hysteresis State Machine)
        # Pha A: Bắt đầu chạm (Khoảng cách co lại <= pinch_thresh)
        if not self.is_pinched and dist_ratio <= self.pinch_thresh:
            self.is_pinched = True
            self.tap_count += 1
            self.last_tap_time = now

            # Nếu đây là cú chạm thứ 2 -> ĐÃ ĐỦ ĐIỀU KIỆN KÝ HIỆU SỐ 10!
            if self.tap_count >= 2:
                self.reset()
                self.last_success_time = now
                return True, {
                    "name": self.gesture_name,
                    "confidence": 92.5,
                    "distance": round(dist_ratio, 3),
                    "type": "ĐỘNG",
                    "hand": "Active",
                    "candidates": [{"name": self.gesture_name, "confidence": 92.5}]
                }

            # Nếu mới chạm lần 1 -> Đang thực hiện
            return False, {
                "name": "Đang thực hiện (Chạm 1/2)...",
                "confidence": 50.0,
                "distance": round(dist_ratio, 3),
                "type": "ĐỘNG",
                "in_motion": True
            }

        # Pha B: Nhả ngón tay ra (Khoảng cách mở rộng >= release_thresh)
        elif self.is_pinched and dist_ratio >= self.release_thresh:
            self.is_pinched = False

        # Nếu người dùng đang ở giữa lần chạm 1 và lần chạm 2 (đang mở tay)
        if self.tap_count == 1:
            return False, {
                "name": "Đang thực hiện (Chờ chạm lần 2)...",
                "confidence": 50.0,
                "distance": round(dist_ratio, 3),
                "type": "ĐỘNG",
                "in_motion": True
            }

        # Nếu giữ nguyên ngón tay đứng yên hoặc không làm gì -> Không có sự kiện
        return False, None

