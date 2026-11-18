"""
Standalone Demo for Static Gesture Recognition
==============================================
Chạy thử nghiệm độc lập bộ nhận diện cử chỉ tĩnh:
- Tự động nạp các mẫu tĩnh từ thư mục dataset_static/
- Chạy nhận diện trực tiếp qua Webcam bằng MediaPipe Hands (nhẹ và nhanh)
"""

import cv2
import numpy as np
try:
    from .static_recognizer import StaticGestureRecognizer, align_hand_landmarks
except ImportError:
    from BE import StaticGestureRecognizer, align_hand_landmarks

try:
    import mediapipe as mp
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
except ImportError:
    print("[Error]: Cần cài đặt mediapipe: pip install mediapipe")
    exit(1)


def main():
    print("Khởi tạo StaticGestureRecognizer...")
    recognizer = StaticGestureRecognizer()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error]: Không thể mở webcam!")
        return

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ) as hands:
        print("\n=== ĐANG CHẠY DEMO CỬ CHỈ TĨNH ===")
        print("Nhấn 'q' trên cửa sổ camera để thoát.\n")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    pred = recognizer.recognize_frame(hand_landmarks)

                    if pred and pred["confidence"] >= 35.0:
                        name = pred["name"].upper()
                        conf = pred["confidence"]
                        dist = pred["distance"]
                        color = (0, 255, 0) if conf >= 65.0 else (0, 200, 255)
                        cv2.putText(
                            frame,
                            f"STAT: {name} ({conf:.0f}%) dist: {dist:.2f}",
                            (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.0,
                            color,
                            2,
                            cv2.LINE_AA
                        )

            cv2.imshow("Static Gesture Demo (Standalone)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

