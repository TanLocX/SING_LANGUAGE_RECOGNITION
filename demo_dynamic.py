"""
Standalone Demo for Dynamic Gesture Recognition (Kiểm thử Cử chỉ Động Độc Lập)
==============================================================================
Script gọn nhẹ chạy trực tiếp bằng OpenCV + MediaPipe Holistic:
  - Tự động nạp các mẫu cử chỉ động trong thư mục `dataset/`
  - Tích hợp Kinematic Motion Spotter: Theo dõi trạng thái IDLE / MOVING / COMPLETED
  - Hiển thị thanh đo vận tốc chuyển động và kết quả DTW trên màn hình
  - Nhấn 'q' để thoát, 'c' để xóa bộ đệm nhận diện
"""

import os
import sys
import time

# Giảm bớt cảnh báo log
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import cv2
import numpy as np

from BE import (
    HolisticTracker,
    OnnxTracker,
    extract_keypoints,
    GestureDatasetManager,
    DynamicGestureRecognizer,
    KinematicMotionSpotter,
    MotionState
)


def main():
    print("=" * 60)
    print("🚀 KHỞI ĐỘNG KIỂM THỬ CỬ CHỈ ĐỘNG (DYNAMIC GESTURE SPOTTER)")
    print("=" * 60)

    # 1. Nạp CSDL cử chỉ động
    dm = GestureDatasetManager(dataset_dirs=["dataset"])
    dm.load_all_templates()
    dynamic_templates = dm.dynamic_templates

    print(f"\n📂 Đã nạp {len(dynamic_templates)} nhãn cử chỉ động: {list(dynamic_templates.keys())}")
    for name, sample_list in dynamic_templates.items():
        print(f"   • '{name}': {len(sample_list)} mẫu chuỗi (.npy)")

    if not dynamic_templates:
        print("\n⚠️ CẢNH BÁO: Thư mục 'dataset/' hiện chưa có mẫu cử chỉ động nào!")
        print("   Hãy chắc chắn rằng có ít nhất 1 thư mục cử chỉ (vd: 'dataset/10/').")

    # 2. Khởi tạo Engine nhận diện & Motion Spotter
    recognizer = DynamicGestureRecognizer(window_size=40, target_length=30)
    recognizer.update_templates(dynamic_templates)

    spotter = KinematicMotionSpotter(
        velocity_start_threshold=0.015,
        velocity_stop_threshold=0.008,
        min_motion_frames=10,
        settle_frames_needed=4
    )

    # 3. Khởi tạo Tracker & Camera
    print("\n🎥 Đang mở Webcam...")
    try:
        tracker = OnnxTracker(use_gpu=True)
        print("⚡ Khởi chạy thành công GPU Tracker RTX 3050 (DirectML + Pose Lite)")
    except Exception as e:
        print(f"💻 Dùng CPU MediaPipe Holistic ({e})")
        tracker = HolisticTracker()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("❌ LỖI: Không thể mở webcam!")
            return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("\n✅ WEBCAM ĐÃ SẴN SÀNG!")
    print("   👉 Đưa tay lên làm cử chỉ (vd: cử chỉ lắc ngón cái Số 10)")
    print("   👉 Phím [Q]: Thoát")
    print("   👉 Phím [C]: Xóa bộ đệm kết quả\n")

    last_pred_text = "CHƯA CÓ KẾT QUẢ"
    last_pred_conf = 0.0
    last_pred_time = 0

    fps_counter = 0
    fps_timer = time.time()
    current_fps = 0.0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        fps_counter += 1
        if time.time() - fps_timer >= 1.0:
            current_fps = fps_counter / (time.time() - fps_timer)
            fps_counter = 0
            fps_timer = time.time()

        # Xử lý landmarks qua MediaPipe
        results, _ = tracker.process_frame(
            frame,
            show_hands=True,
            show_pose=True,
            show_face=False,
            mirror=False
        )

        # Lật gương hiển thị để tự nhiên như soi gương
        display_frame = cv2.flip(frame, 1)
        vec_1662 = extract_keypoints(results)

        # Xử lý phân đoạn động học (Motion Spotter)
        state, completed_seq, vel = spotter.process_frame(vec_1662)

        # Khi cử chỉ vừa kết thúc (COMPLETED) -> Chấm điểm ngay lập tức
        if state == MotionState.COMPLETED and completed_seq is not None:
            preds = recognizer.classify_sequence(completed_seq)
            if preds and preds[0]["confidence"] >= 35.0:
                top = preds[0]
                last_pred_text = f"{top['name'].upper()} ({top['confidence']}%)"
                last_pred_conf = top["confidence"]
                last_pred_time = time.time()
                print(f"[SPOTTER HIT!]: Cử chỉ '{top['name']}' - Độ tin cậy: {top['confidence']}% (Sai số DTW: {top['distance']})")

        # Sliding Window DTW liên tục (bắt trong lúc đang di chuyển)
        dyn_match, is_moving = recognizer.process_frame(vec_1662, force_dynamic=True)
        if dyn_match is not None and dyn_match["confidence"] >= 45.0:
            last_pred_text = f"{dyn_match['name'].upper()} ({dyn_match['confidence']}%)"
            last_pred_conf = dyn_match["confidence"]
            last_pred_time = time.time()
            print(f"[SLIDING DTW HIT!]: Cử chỉ '{dyn_match['name']}' - Độ tin cậy: {dyn_match['confidence']}%")

        # ================= VẼ GIAO DIỆN HUD =================
        h, w = display_frame.shape[:2]

        # Trạng thái Motion Spotter
        state_color = (150, 150, 150) # IDLE - Xám
        if state == MotionState.MOVING or is_moving:
            state_color = (0, 220, 255) # MOVING - Vàng cam
            state_text = f"DANG THUC HIEN (Vel: {vel:.3f})"
        elif state == MotionState.COOLDOWN:
            state_color = (255, 100, 100)
            state_text = "DANG COOLDOWN..."
        else:
            state_text = "SAN SANG (IDLE)"

        cv2.rectangle(display_frame, (15, 15), (w - 15, 95), (20, 24, 30), -1)
        cv2.rectangle(display_frame, (15, 15), (w - 15, 95), (60, 70, 85), 2)

        # In trạng thái
        cv2.circle(display_frame, (35, 42), 8, state_color, -1)
        cv2.putText(display_frame, f"TRANG THAI: {state_text}", (55, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.65, state_color, 2)

        # In kết quả nhận diện
        res_color = (0, 255, 180) if last_pred_conf >= 60.0 else (50, 200, 255)
        cv2.putText(display_frame, f"KET QUA: {last_pred_text}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, res_color, 2)

        # In FPS góc phải
        cv2.putText(display_frame, f"{current_fps:.1f} FPS", (w - 120, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Dynamic Gesture Spotter & Recognizer (FG_1.1)", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('c'):
            last_pred_text = "CHƯA CÓ KẾT QUẢ"
            last_pred_conf = 0.0
            recognizer.clear_buffer()
            spotter.reset()
            print("[Cleared buffer]")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

