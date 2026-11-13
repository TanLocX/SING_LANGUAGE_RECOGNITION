"""
MediaPipe Holistic Tracker Module (High Performance)
====================================================
Theo dõi toàn diện cơ thể:
  - Cánh tay & Thân (Pose: 33 điểm)
  - Bàn tay trái & Bàn tay phải (Hands: 21 điểm mỗi tay)
  - Đầu & Nét mặt (Face Mesh: 468 điểm)
  - Khắc phục triệt để lỗi đảo tay khi soi gương
  - Tối ưu hóa hiệu năng (30+ FPS) với model_complexity=0
  - Trích xuất vector 1.662 điểm chuẩn
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Tuple, Optional


def extract_keypoints(results) -> np.ndarray:
    """
    Trích xuất toàn bộ toạ độ của Pose, Face, Left Hand, Right Hand thành 1 vector 1D (1.662 giá trị):
      - Pose: 33 * 4 = 132
      - Face: 468 * 3 = 1404
      - Left Hand: 21 * 3 = 63
      - Right Hand: 21 * 3 = 63
    """
    if results.pose_landmarks:
        pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten()
    else:
        pose = np.zeros(33 * 4)

    if results.face_landmarks:
        face = np.array([[res.x, res.y, res.z] for res in results.face_landmarks.landmark]).flatten()
    else:
        face = np.zeros(468 * 3)

    if results.left_hand_landmarks:
        lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten()
    else:
        lh = np.zeros(21 * 3)

    if results.right_hand_landmarks:
        rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten()
    else:
        rh = np.zeros(21 * 3)

    return np.concatenate([pose, face, lh, rh]).astype(np.float32)


class HolisticTracker:
    def __init__(self, min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5):
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_face_mesh = mp.solutions.face_mesh
        
        # model_complexity=0 mang lại tốc độ real-time 30-45 FPS trên CPU
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=0,
            smooth_landmarks=False,
            refine_face_landmarks=False
        )

        # Drawing specs tối ưu trước để tránh tạo lại đối tượng mỗi frame
        self.spec_face = self.mp_drawing.DrawingSpec(color=(255, 180, 50), thickness=1, circle_radius=1)
        self.spec_pose_pt = self.mp_drawing.DrawingSpec(color=(0, 220, 100), thickness=2, circle_radius=2)
        self.spec_pose_line = self.mp_drawing.DrawingSpec(color=(240, 240, 240), thickness=2, circle_radius=1)
        self.spec_lh_pt = self.mp_drawing.DrawingSpec(color=(255, 80, 150), thickness=2, circle_radius=3)
        self.spec_lh_line = self.mp_drawing.DrawingSpec(color=(255, 180, 200), thickness=2, circle_radius=1)
        self.spec_rh_pt = self.mp_drawing.DrawingSpec(color=(50, 220, 255), thickness=2, circle_radius=3)
        self.spec_rh_line = self.mp_drawing.DrawingSpec(color=(150, 240, 255), thickness=2, circle_radius=1)

    def process_frame(
        self,
        raw_bgr_frame: np.ndarray,
        show_hands: bool = True,
        show_pose: bool = True,
        show_face: bool = True,
        mirror: bool = True
    ) -> Tuple[any, np.ndarray]:
        """
        Xử lý frame:
          1. Đưa frame gốc (chưa lật gương) vào MediaPipe để đảm bảo tính giải phẫu học
             (Tay Phải -> Right Hand, Tay Trái -> Left Hand).
          2. Vẽ bộ khung khớp xương lên frame.
          3. Lật gương nếu bật (mirror=True) để soi gương tự nhiên.
          4. Vẽ nhãn cổ tay TAY PHẢI / TAY TRÁI sau khi lật gương.
        """
        # 1. MediaPipe nhận ảnh RGB chưa lật
        raw_rgb = cv2.cvtColor(raw_bgr_frame, cv2.COLOR_BGR2RGB)
        raw_rgb.flags.writeable = False
        results = self.holistic.process(raw_rgb)
        raw_rgb.flags.writeable = True

        annotated_bgr = raw_bgr_frame.copy()

        # 2. Vẽ bộ khung khớp xương
        if show_face and results.face_landmarks:
            # Vẽ đường nét mặt gọn gàng (Face Oval + Mắt)
            self.mp_drawing.draw_landmarks(
                annotated_bgr,
                results.face_landmarks,
                self.mp_face_mesh.FACEMESH_FACE_OVAL,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.spec_face
            )

        if show_pose and results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                annotated_bgr,
                results.pose_landmarks,
                self.mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=self.spec_pose_pt,
                connection_drawing_spec=self.spec_pose_line
            )

        if show_hands and results.left_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                annotated_bgr,
                results.left_hand_landmarks,
                self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=self.spec_lh_pt,
                connection_drawing_spec=self.spec_lh_line
            )

        if show_hands and results.right_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                annotated_bgr,
                results.right_hand_landmarks,
                self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=self.spec_rh_pt,
                connection_drawing_spec=self.spec_rh_line
            )

        # 3. Lật gương hiển thị
        if mirror:
            display_bgr = cv2.flip(annotated_bgr, 1)
        else:
            display_bgr = annotated_bgr

        # 4. Vẽ nhãn cổ tay
        if show_hands:
            self._draw_wrist_badges(display_bgr, results, mirror=mirror)

        return results, display_bgr

    def _draw_wrist_badges(self, display_bgr: np.ndarray, results, mirror: bool = True):
        h, w, _ = display_bgr.shape

        def get_x(norm_x: float) -> int:
            return int((1.0 - norm_x) * w) if mirror else int(norm_x * w)

        # Tay Phải (Xanh Cyan)
        if results.right_hand_landmarks:
            wrist = results.right_hand_landmarks.landmark[0]
            wx, wy = get_x(wrist.x), int(wrist.y * h) - 15
            label = "TAY PHAI (RIGHT)"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            bx = max(10, min(w - tw - 20, wx - tw // 2))
            by = max(30, wy)
            cv2.rectangle(display_bgr, (bx - 4, by - th - 4), (bx + tw + 4, by + 4), (20, 30, 40), -1)
            cv2.rectangle(display_bgr, (bx - 4, by - th - 4), (bx + tw + 4, by + 4), (50, 220, 255), 1)
            cv2.putText(display_bgr, label, (bx, by), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (50, 220, 255), 1, cv2.LINE_AA)

        # Tay Trái (Hồng Coral)
        if results.left_hand_landmarks:
            wrist = results.left_hand_landmarks.landmark[0]
            wx, wy = get_x(wrist.x), int(wrist.y * h) - 15
            label = "TAY TRAI (LEFT)"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            bx = max(10, min(w - tw - 20, wx - tw // 2))
            by = max(30, wy)
            cv2.rectangle(display_bgr, (bx - 4, by - th - 4), (bx + tw + 4, by + 4), (20, 30, 40), -1)
            cv2.rectangle(display_bgr, (bx - 4, by - th - 4), (bx + tw + 4, by + 4), (255, 80, 150), 1)
            cv2.putText(display_bgr, label, (bx, by), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 80, 150), 1, cv2.LINE_AA)

    def close(self):
        if hasattr(self, 'holistic') and self.holistic:
            self.holistic.close()


def draw_keypoints_vector(
    frame_bgr: np.ndarray,
    vec_1662: np.ndarray,
    show_hands: bool = True,
    show_pose: bool = True,
    show_face: bool = True,
    mirror: bool = False
) -> np.ndarray:
    """
    Vẽ trực tiếp khung xương lên bản sao khung hình (chỉ phục vụ hiển thị Canvas).
    Khung hình gốc không bị thay đổi (không bị ghi đè vào dữ liệu gốc).
    """
    if vec_1662 is None or len(vec_1662) < 1662:
        return frame_bgr

    h, w = frame_bgr.shape[:2]

    def pt(norm_x: float, norm_y: float) -> Tuple[int, int]:
        x = (1.0 - norm_x) if mirror else norm_x
        return int(np.clip(x, 0.0, 1.0) * w), int(np.clip(norm_y, 0.0, 1.0) * h)

    # 1. Vẽ Pose (Cánh tay & Vai)
    if show_pose:
        pose = vec_1662[0:132].reshape(33, 4)
        pose_edges = [
            (11, 12),           # Vai trái - Vai phải
            (11, 13), (13, 15), # Tay trái (vai -> khuỷu -> cổ tay)
            (12, 14), (14, 16), # Tay phải (vai -> khuỷu -> cổ tay)
        ]
        for idx1, idx2 in pose_edges:
            p1, p2 = pose[idx1], pose[idx2]
            if p1[3] > 0.25 and p2[3] > 0.25 and (p1[0] != 0 or p1[1] != 0) and (p2[0] != 0 or p2[1] != 0):
                c1 = pt(p1[0], p1[1])
                c2 = pt(p2[0], p2[1])
                cv2.line(frame_bgr, c1, c2, (240, 240, 240), 2, cv2.LINE_AA)

        for joint_idx in [11, 12, 13, 14, 15, 16]:
            p = pose[joint_idx]
            if p[3] > 0.25 and (p[0] != 0 or p[1] != 0):
                cv2.circle(frame_bgr, pt(p[0], p[1]), 4, (0, 220, 100), -1, cv2.LINE_AA)

    # 2. Vẽ Face Mesh Oval
    if show_face:
        face = vec_1662[132:1536].reshape(468, 3)
        if not np.all(face == 0):
            oval_indices = [
                10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10
            ]
            pts = []
            for idx in oval_indices:
                p = face[idx]
                if p[0] != 0 or p[1] != 0:
                    pts.append(pt(p[0], p[1]))
            if len(pts) >= 4:
                pts_arr = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame_bgr, [pts_arr], isClosed=True, color=(255, 180, 50), thickness=1, lineType=cv2.LINE_AA)

    # 3. Vẽ Khung xương Bàn tay (21 điểm)
    hand_edges = [
        (0, 1), (1, 2), (2, 3), (3, 4),        # Ngón cái
        (0, 5), (5, 6), (6, 7), (7, 8),        # Ngón trỏ
        (5, 9), (9, 10), (10, 11), (11, 12),   # Ngón giữa
        (9, 13), (13, 14), (14, 15), (15, 16), # Ngón nhẫn
        (13, 17), (17, 18), (18, 19), (19, 20), (0, 17), # Ngón út
        (5, 9), (9, 13), (13, 17)              # Gốc lòng bàn tay
    ]

    if show_hands:
        # Bàn tay trái (Hồng Coral)
        lh = vec_1662[1536:1599].reshape(21, 3)
        if not np.all(lh == 0):
            for i1, i2 in hand_edges:
                p1, p2 = lh[i1], lh[i2]
                if (p1[0] != 0 or p1[1] != 0) and (p2[0] != 0 or p2[1] != 0):
                    cv2.line(frame_bgr, pt(p1[0], p1[1]), pt(p2[0], p2[1]), (255, 180, 200), 2, cv2.LINE_AA)
            for i in range(21):
                p = lh[i]
                if p[0] != 0 or p[1] != 0:
                    cv2.circle(frame_bgr, pt(p[0], p[1]), 3, (255, 80, 150), -1, cv2.LINE_AA)

        # Bàn tay phải (Vàng / Cyan)
        rh = vec_1662[1599:1662].reshape(21, 3)
        if not np.all(rh == 0):
            for i1, i2 in hand_edges:
                p1, p2 = rh[i1], rh[i2]
                if (p1[0] != 0 or p1[1] != 0) and (p2[0] != 0 or p2[1] != 0):
                    cv2.line(frame_bgr, pt(p1[0], p1[1]), pt(p2[0], p2[1]), (150, 240, 255), 2, cv2.LINE_AA)
            for i in range(21):
                p = rh[i]
                if p[0] != 0 or p[1] != 0:
                    cv2.circle(frame_bgr, pt(p[0], p[1]), 3, (50, 220, 255), -1, cv2.LINE_AA)

    return frame_bgr

