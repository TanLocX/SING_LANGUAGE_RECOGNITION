"""
Sign Language Recognition - Step 1: MediaPipe Holistic Demo
============================================================
Theo dõi đồng thời:
  1. Cánh tay, vai & cơ thể (Pose Landmarks: 33 điểm)
  2. Bàn tay trái (Left Hand Landmarks: 21 điểm)
  3. Bàn tay phải (Right Hand Landmarks: 21 điểm)
  4. Đầu và nét mặt (Face Mesh: 468 điểm)

ĐÃ KHẮC PHỤC LỖI NHẬN DIỆN SAI TAY (LẬT GƯƠNG):
  - Khung hình gốc từ camera được đưa vào MediaPipe trước (chuẩn góc nhìn giải phẫu học).
  - Tay Phải luôn được gán đúng vào Right Hand, Tay Trái luôn gán đúng vào Left Hand.
  - Sau đó mới lật gương hiển thị (Mirror) để người dùng thao tác tự nhiên như soi gương.
  - Có gắn nhãn nổi (floating badge) 'TAY PHẢI' và 'TAY TRÁI' ngay tại cổ tay.

Phím tắt:
  [F] Bật/tắt Face Mesh
  [H] Bật/tắt Bàn tay (Hands)
  [P] Bật/tắt Dáng điệu/Cánh tay (Pose)
  [M] Bật/tắt Lật gương (Mirror)
  [S] Lưu mẫu frame landmarks hiện tại ra file .npy
  [Q / ESC] Thoát
"""

import os
import sys
import time
from datetime import datetime

# Ẩn các log cảnh báo không cần thiết của TensorFlow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import cv2
import mediapipe as mp
import numpy as np


def extract_keypoints(results) -> np.ndarray:
    """
    Trích xuất toàn bộ toạ độ của Pose, Face, Left Hand, Right Hand thành 1 vector 1D (1662 giá trị).
    Nếu bộ phận nào không xuất hiện trong khung hình thì điền giá trị 0.
    - Pose: 33 điểm * 4 (x, y, z, visibility) = 132
    - Face: 468 điểm * 3 (x, y, z) = 1404
    - Left Hand: 21 điểm * 3 (x, y, z) = 63 (ĐÚNG TAY TRÁI CỦA NGƯỜI DÙNG)
    - Right Hand: 21 điểm * 3 (x, y, z) = 63 (ĐÚNG TAY PHẢI CỦA NGƯỜI DÙNG)
    Tổng cộng: 1662 features / frame.
    """
    # 1. Pose (33 * 4 = 132)
    if results.pose_landmarks:
        pose = np.array(
            [[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]
        ).flatten()
    else:
        pose = np.zeros(33 * 4)

    # 2. Face (468 * 3 = 1404)
    if results.face_landmarks:
        face = np.array(
            [[res.x, res.y, res.z] for res in results.face_landmarks.landmark]
        ).flatten()
    else:
        face = np.zeros(468 * 3)

    # 3. Left Hand (21 * 3 = 63)
    if results.left_hand_landmarks:
        lh = np.array(
            [[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]
        ).flatten()
    else:
        lh = np.zeros(21 * 3)

    # 4. Right Hand (21 * 3 = 63)
    if results.right_hand_landmarks:
        rh = np.array(
            [[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]
        ).flatten()
    else:
        rh = np.zeros(21 * 3)

    return np.concatenate([pose, face, lh, rh])


def draw_styled_landmarks(
    image: np.ndarray,
    results,
    mp_holistic,
    mp_drawing,
    show_face: bool = True,
    show_hands: bool = True,
    show_pose: bool = True,
):
    """Vẽ các khớp xương và lưới điểm lên khung hình với màu sắc phân biệt."""
    # 1. Vẽ Face Mesh (Đầu và biểu cảm)
    if show_face and results.face_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.face_landmarks,
            mp_holistic.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing.DrawingSpec(
                color=(180, 200, 220), thickness=1, circle_radius=1
            ),
        )
        mp_drawing.draw_landmarks(
            image,
            results.face_landmarks,
            mp_holistic.FACEMESH_CONTOURS,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing.DrawingSpec(
                color=(255, 180, 50), thickness=1, circle_radius=1
            ),
        )

    # 2. Vẽ Pose (Cánh tay, vai, ngực)
    if show_pose and results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(
                color=(0, 220, 100), thickness=3, circle_radius=3
            ),
            connection_drawing_spec=mp_drawing.DrawingSpec(
                color=(240, 240, 240), thickness=2, circle_radius=2
            ),
        )

    # 3. Vẽ Bàn tay trái (Màu Hồng / Coral)
    if show_hands and results.left_hand_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.left_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(
                color=(255, 80, 150), thickness=3, circle_radius=4
            ),
            connection_drawing_spec=mp_drawing.DrawingSpec(
                color=(255, 180, 200), thickness=2, circle_radius=2
            ),
        )

    # 4. Vẽ Bàn tay phải (Màu Xanh Cyan / Turquoise)
    if show_hands and results.right_hand_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.right_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(
                color=(50, 220, 255), thickness=3, circle_radius=4
            ),
            connection_drawing_spec=mp_drawing.DrawingSpec(
                color=(150, 240, 255), thickness=2, circle_radius=2
            ),
        )


def draw_hand_labels(image: np.ndarray, results, mirror: bool):
    """Vẽ nhãn nổi hiển thị rõ 'TAY PHẢI' và 'TAY TRÁI' ngay vị trí cổ tay."""
    h, w, _ = image.shape

    # Helper tính toạ độ X sau khi lật gương
    def get_x(norm_x: float) -> int:
        if mirror:
            return int((1.0 - norm_x) * w)
        return int(norm_x * w)

    # Nhãn Tay Phải (Cyan)
    if results.right_hand_landmarks:
        wrist = results.right_hand_landmarks.landmark[0]
        wx = get_x(wrist.x)
        wy = int(wrist.y * h) - 15

        label = "TAY PHAI (RIGHT)"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 2)
        bx = max(10, min(w - tw - 20, wx - tw // 2))
        by = max(30, wy)

        # Hộp nền nhãn
        cv2.rectangle(image, (bx - 6, by - th - 6), (bx + tw + 6, by + 6), (20, 30, 40), -1)
        cv2.rectangle(image, (bx - 6, by - th - 6), (bx + tw + 6, by + 6), (50, 220, 255), 1)
        cv2.putText(
            image,
            label,
            (bx, by),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (50, 220, 255),
            2,
            cv2.LINE_AA,
        )

    # Nhãn Tay Trái (Pink)
    if results.left_hand_landmarks:
        wrist = results.left_hand_landmarks.landmark[0]
        wx = get_x(wrist.x)
        wy = int(wrist.y * h) - 15

        label = "TAY TRAI (LEFT)"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 2)
        bx = max(10, min(w - tw - 20, wx - tw // 2))
        by = max(30, wy)

        # Hộp nền nhãn
        cv2.rectangle(image, (bx - 6, by - th - 6), (bx + tw + 6, by + 6), (20, 30, 40), -1)
        cv2.rectangle(image, (bx - 6, by - th - 6), (bx + tw + 6, by + 6), (255, 80, 150), 1)
        cv2.putText(
            image,
            label,
            (bx, by),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (255, 80, 150),
            2,
            cv2.LINE_AA,
        )


def draw_hud(
    image: np.ndarray,
    results,
    fps: float,
    show_face: bool,
    show_hands: bool,
    show_pose: bool,
    mirror: bool,
    saved_msg: str,
):
    """Vẽ bảng thông tin trạng thái theo dõi và phím tắt."""
    h, w, _ = image.shape

    # 1. Header panel (góc trên bên trái)
    overlay = image.copy()
    cv2.rectangle(overlay, (15, 15), (380, 230), (18, 22, 32), -1)
    cv2.addWeighted(overlay, 0.8, image, 0.2, 0, image)
    cv2.rectangle(image, (15, 15), (380, 230), (90, 110, 140), 1)

    cv2.putText(
        image,
        "SIGN LANGUAGE - HOLISTIC DEMO",
        (28, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    # Trạng thái FPS & Chế độ Mirror
    mirror_txt = "MIRROR: ON" if mirror else "MIRROR: OFF"
    cv2.putText(
        image,
        f"FPS: {fps:.1f} | {mirror_txt}",
        (28, 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (0, 255, 180),
        1,
        cv2.LINE_AA,
    )

    # Trạng thái từng bộ phận
    def status_line(y, label, active, detected, dot_color=(80, 240, 120)):
        text = f"{label}: "
        if not active:
            color = (120, 120, 120)
            text += "[OFF]"
        elif detected:
            color = dot_color
            text += "[DETECTED]"
        else:
            color = (100, 120, 240)
            text += "[SEARCHING...]"
        cv2.putText(image, text, (28, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

    status_line(95, "Pose (Canh tay & Vai)", show_pose, results.pose_landmarks is not None)
    # Right hand: Xanh Cyan
    status_line(
        122,
        "Right Hand (Tay phai)",
        show_hands,
        results.right_hand_landmarks is not None,
        dot_color=(50, 220, 255),
    )
    # Left hand: Hồng Coral
    status_line(
        149,
        "Left Hand (Tay trai)",
        show_hands,
        results.left_hand_landmarks is not None,
        dot_color=(255, 80, 150),
    )
    status_line(176, "Face (Dau & Net mat)", show_face, results.face_landmarks is not None)

    # Vector length
    keypoints = extract_keypoints(results)
    cv2.putText(
        image,
        f"Vector size: {len(keypoints)} floats / frame",
        (28, 208),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (220, 220, 220),
        1,
        cv2.LINE_AA,
    )

    # 2. Controls panel (góc dưới)
    overlay2 = image.copy()
    cv2.rectangle(overlay2, (15, h - 50), (w - 15, h - 15), (18, 22, 32), -1)
    cv2.addWeighted(overlay2, 0.8, image, 0.2, 0, image)
    cv2.rectangle(image, (15, h - 50), (w - 15, h - 15), (90, 110, 140), 1)

    controls_text = (
        "[P] Pose: " + ("ON" if show_pose else "OFF") +
        " | [H] Hands: " + ("ON" if show_hands else "OFF") +
        " | [F] Face: " + ("ON" if show_face else "OFF") +
        " | [M] Mirror: " + ("ON" if mirror else "OFF") +
        " | [S] Save .npy | [Q] Quit"
    )
    cv2.putText(
        image,
        controls_text,
        (25, h - 27),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.46,
        (240, 240, 240),
        1,
        cv2.LINE_AA,
    )

    # 3. Thông báo lưu file (nếu có)
    if saved_msg:
        cv2.putText(
            image,
            saved_msg,
            (w // 2 - 150, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )


def main():
    camera_index = 0
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"[CẢNH BÁO] Không mở được camera {camera_index}, thử camera 1...")
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("[LỖI] Không tìm thấy camera nào hoạt động!")
            sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Cài đặt hiển thị
    show_face = True
    show_hands = True
    show_pose = True
    mirror = True

    saved_msg = ""
    saved_time = 0.0

    output_dir = "collected_samples"
    os.makedirs(output_dir, exist_ok=True)

    mp_holistic = mp.solutions.holistic
    mp_drawing = mp.solutions.drawing_utils

    prev_time = time.time()
    fps = 30.0

    print("=" * 60)
    print("Khởi tạo MediaPipe Holistic cho Nhận diện Ngôn ngữ Ký hiệu...")
    print("ĐÃ FIX LỖI NHẬN DIỆN TAY:")
    print("  - Phân loại chính xác Tay Phải (Right) & Tay Trái (Left)")
    print("  - Có nhãn nổi theo sau cổ tay")
    print("Các phím bấm:")
    print("  [P] : Bật/tắt theo dõi Cánh tay & Thân (Pose)")
    print("  [H] : Bật/tắt theo dõi Bàn tay (Hands)")
    print("  [F] : Bật/tắt theo dõi Đầu & Khuôn mặt (Face)")
    print("  [M] : Bật/tắt chế độ lật gương (Mirror)")
    print("  [S] : Lưu vector landmarks của frame hiện tại (.npy)")
    print("  [Q] hoặc [ESC] : Thoát ứng dụng")
    print("=" * 60)

    with mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1,
    ) as holistic:
        while cap.isOpened():
            ret, raw_frame = cap.read()
            if not ret:
                print("[LỖI] Không nhận được frame từ webcam.")
                break

            # Tính FPS
            curr_time = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(1e-5, (curr_time - prev_time)))
            prev_time = curr_time

            # QUAN TRỌNG:
            # Đưa frame GỐC (chưa lật gương) vào MediaPipe Holistic
            # để đảm bảo nhận diện đúng 100% giải phẫu học: Tay Phải ra Right Hand, Tay Trái ra Left Hand!
            raw_rgb = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
            raw_rgb.flags.writeable = False
            results = holistic.process(raw_rgb)
            raw_rgb.flags.writeable = True

            # Vẽ các khớp xương lên frame trước khi lật gương
            draw_styled_landmarks(
                raw_frame,
                results,
                mp_holistic,
                mp_drawing,
                show_face=show_face,
                show_hands=show_hands,
                show_pose=show_pose,
            )

            # Nếu bật lật gương, ta lật toàn bộ khung hình đã vẽ skeleton
            # để người dùng nhìn như đang soi gương tự nhiên
            if mirror:
                display_frame = cv2.flip(raw_frame, 1)
            else:
                display_frame = raw_frame

            # Vẽ nhãn nổi TAY PHẢI / TAY TRÁI (vẽ sau khi lật để chữ không bị ngược)
            if show_hands:
                draw_hand_labels(display_frame, results, mirror=mirror)

            # Hết hạn thông báo lưu sau 2 giây
            if saved_msg and (curr_time - saved_time > 2.0):
                saved_msg = ""

            # Vẽ HUD thông số
            draw_hud(
                display_frame,
                results,
                fps,
                show_face,
                show_hands,
                show_pose,
                mirror,
                saved_msg,
            )

            cv2.imshow("Sign Language Recognition - MediaPipe Holistic", display_frame)

            # Xử lý phím bấm
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                break
            elif key in (ord("p"), ord("P")):
                show_pose = not show_pose
            elif key in (ord("h"), ord("H")):
                show_hands = not show_hands
            elif key in (ord("f"), ord("F")):
                show_face = not show_face
            elif key in (ord("m"), ord("M")):
                mirror = not mirror
            elif key in (ord("s"), ord("S")):
                # Trích xuất và lưu vector landmarks
                keypoints = extract_keypoints(results)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filepath = os.path.join(output_dir, f"sample_{timestamp}.npy")
                np.save(filepath, keypoints)
                saved_msg = f"Saved: {os.path.basename(filepath)}"
                saved_time = curr_time
                print(f"[ĐÃ LƯU] Vector shape: {keypoints.shape} -> {filepath}")

    cap.release()
    cv2.destroyAllWindows()
    print("Đã đóng chương trình.")


if __name__ == "__main__":
    main()
