# Static Gesture Module (Mô-đun Nhận diện Cử chỉ Tĩnh)

Thư mục này chứa toàn bộ dữ liệu và logic nhận diện cử chỉ tĩnh (Hand Shape / Single-frame), được tách biệt hoàn toàn khỏi hệ thống cử chỉ động chính (`FG_1.1`).

## 📁 Cấu trúc thư mục:
- `dataset_static/`: Chứa các mẫu mảng NumPy `.npy` của các chữ số và chữ cái tĩnh (`0, 1, 2, 3, 4, 5, 6, 7, 8, 9, a, b`).
- `static_recognizer.py`: Chứa class `StaticGestureRecognizer` và thuật toán chuẩn hóa đồng dạng:
  - Tịnh tiến về cổ tay (Translation Invariance).
  - Chuẩn hóa tỷ lệ theo chiều dài xương bàn tay (Scale Invariance).
  - Xoay bàn tay thẳng đứng (Rotation Invariance).
  - So khớp đối xứng Mirror-X (dùng cho cả tay Trái và Phải).
- `demo_static.py`: File chạy demo độc lập qua webcam để kiểm tra cử chỉ tĩnh.
- `dataset.npz`: File dữ liệu nén tĩnh cũ.

## 🚀 Cách chạy demo độc lập:
```bash
python static_gesture_module/demo_static.py
```

