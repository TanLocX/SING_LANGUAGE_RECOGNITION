"""
Live Webcam & Real-time Gesture Recognition Controller
======================================================
Quản lý luồng hoạt động của Webcam:
  - Khởi tạo & giải phóng camera (30 FPS)
  - Luồng ngầm xử lý MediaPipe Holistic độc lập
  - Nhận diện cử chỉ trực tiếp (Live Recognition)
  - Đếm ngược 3s và ghi nhận mẫu webcam vào bộ nhớ tạm
"""

import time
import threading
import cv2
import numpy as np
from tkinter import messagebox
from BE import extract_keypoints, detect_gesture_motion


class LiveWebcamMixin:
    """
    Mixin chứa toàn bộ logic xử lý Webcam và Nhận diện trực tiếp.
    """

    def toggle_live_recognition_mode(self):
        if self.is_live_rec_mode:
            self.close_live_recognition()
        else:
            self.open_live_recognition()

    def open_live_recognition(self):
        # Dừng phát video nếu đang phát
        self.is_playing = False
        if not self.camera.open(0):
            if not self.camera.open(1):
                messagebox.showerror("Lỗi Camera", "Không thể kết nối với Webcam!")
                return

        self.is_live_rec_mode = True
        self.canvas_panel.webcam_ctrl_frame.pack_forget()
        self.canvas_panel.live_rec_ctrl_frame.pack(fill="x")
        self.canvas_panel.lbl_live_status.configure(
            text="🔴 ĐANG NHẬN DIỆN TRỰC TIẾP QUA WEBCAM (HOLISTIC)", text_color="#A78BFA"
        )
        live_btn = getattr(self, "left_panel", None) and getattr(self.left_panel, "btn_live_rec", None) or getattr(self.top_bar, "btn_live_rec", None)
        if live_btn:
            live_btn.configure(text="⏹ Dừng Nhận Diện", fg_color="#DC2626", hover_color="#B91C1C")
        # Tự động đồng bộ hoá CSDL cử chỉ mới nhất vào RAM Cache của 2 engine
        if hasattr(self, "recognizer") and hasattr(self.recognizer, "sync_engines"):
            self.recognizer.sync_engines(force_reload=True)

        # Khởi chạy luồng ngầm xử lý MediaPipe độc lập (giải phóng UI thread, giữ 30+ FPS)
        self.live_worker_thread = threading.Thread(target=self._live_worker, daemon=True)
        self.live_worker_thread.start()

        self.ui_update_counter = 0
        self._live_recognition_loop()

    def close_live_recognition(self):
        self.is_live_rec_mode = False
        with self.live_frame_lock:
            self.latest_live_frame = None
            self.latest_live_results = None
            self.latest_live_pred = None
            self.last_stable_pred = None
            self.stable_pred_hold_count = 0

        self.camera.release()
        self.canvas_panel.live_rec_ctrl_frame.pack_forget()
        live_btn = getattr(self, "left_panel", None) and getattr(self.left_panel, "btn_live_rec", None) or getattr(self.top_bar, "btn_live_rec", None)
        if live_btn:
            live_btn.configure(text="🎥 Nhận Diện Trực Tiếp", fg_color="#7C3AED", hover_color="#6D28D9")
        self.canvas_panel.lbl_video_canvas.configure(image=None, text="[Màn hình Hiển thị Video / Camera]")
        self.right_panel.lbl_rec_main.configure(text="CHƯA CÓ KẾT QUẢ", text_color="#00FFCC")
        self.right_panel.lbl_rec_confidence.configure(text="Độ tin cậy: --%  |  Sai số: --")
        self.right_panel.lbl_rec_details.configure(text="Cấu trúc: --  |  Số frame khớp: --")
        print("[Live Rec]: Đã dừng nhận diện trực tiếp.")

    def _live_worker(self):
        """
        Luồng nền xử lý MediaPipe và nhận diện độc lập với UI.
        Giúp UI canvas và camera hiển thị đạt trọn vẹn 30 FPS không bao giờ bị nghẽn (drop FPS).
        """
        while self.is_live_rec_mode and self.camera.is_opened():
            ret, raw_frame = self.camera.read_frame()
            if not ret or raw_frame is None:
                time.sleep(0.005)
                continue

            show_hands = bool(self.right_panel.chk_landmarks.get())
            show_pose = bool(self.right_panel.chk_arm_pose.get())
            show_face = bool(self.right_panel.chk_head_tracker.get())

            results, display_bgr = self.tracker.process_frame(
                raw_frame,
                show_hands=show_hands,
                show_pose=show_pose,
                show_face=show_face,
                mirror=True
            )

            # Lấy chế độ nhận diện từ bộ chọn GUI (Tự động / Chỉ Tĩnh / Chỉ Động)
            rec_mode = "auto"
            if hasattr(self.right_panel, "seg_rec_mode"):
                mode_str = self.right_panel.seg_rec_mode.get()
                if "Tĩnh" in mode_str:
                    rec_mode = "static"
                elif "Động" in mode_str:
                    rec_mode = "dynamic"

            # Nhận diện cử chỉ trực tiếp từ frame (khi không trong chế độ quay mẫu)
            live_pred = self.recognizer.recognize_live_frame(results, mode=rec_mode) if not self.is_recording_sample else None

            # Vẽ HUD nhận diện trực tiếp lên khung hình mượt mà không nhấp nháy
            if live_pred and live_pred.get("in_motion"):
                cv2.putText(
                    display_bgr,
                    "DYN: [DANG THUC HIEN...]",
                    (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.80,
                    (0, 220, 255),
                    2,
                    cv2.LINE_AA
                )
            elif live_pred and live_pred["confidence"] >= 30.0:
                pred_name = live_pred["name"].upper()
                conf = live_pred["confidence"]
                g_type = live_pred.get("type", "TĨNH")
                tag_label = "DYN" if g_type == "ĐỘNG" else "STAT"
                color = (0, 255, 200) if conf >= 60.0 else (50, 200, 255)
                cv2.putText(
                    display_bgr,
                    f"[{tag_label}] {pred_name} ({conf:.0f}%)",
                    (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.85,
                    color,
                    2,
                    cv2.LINE_AA
                )

            # Xử lý Quay Mẫu Webcam (Ghi nhận frames sạch và keypoints)
            h, w = display_bgr.shape[:2]
            clean_mirrored = cv2.flip(raw_frame, 1)

            if self.countdown_val > 0:
                # Vẽ vòng tròn và số đếm ngược 3, 2, 1 nổi bật giữa màn hình
                overlay = display_bgr.copy()
                cv2.circle(overlay, (w // 2, h // 2), 70, (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.65, display_bgr, 0.35, 0, display_bgr)
                cv2.circle(display_bgr, (w // 2, h // 2), 70, (0, 220, 255), 4, cv2.LINE_AA)
                cv2.putText(
                    display_bgr,
                    str(self.countdown_val),
                    (w // 2 - 22, h // 2 + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2.6,
                    (0, 255, 255),
                    5,
                    cv2.LINE_AA
                )
            elif self.is_recording_sample:
                # Trích xuất vector 1662 keypoints
                kp = extract_keypoints(results)
                # CHỈ LƯU KHUNG HÌNH GỐC SẠCH (KHÔNG KHUNG XƯƠNG, KHÔNG TEXT) VÀO BỘ NHỚ
                self.recorded_frames.append(clean_mirrored.copy())
                self.recorded_keypoints.append(kp)

                # Hiệu ứng nhấp nháy REC màu đỏ góc trên
                n_rec = len(self.recorded_frames)
                rec_sec = n_rec / 30.0
                cv2.circle(display_bgr, (w - 200, 35), 8, (0, 0, 255), -1)
                cv2.putText(
                    display_bgr,
                    f"REC: {n_rec}f ({rec_sec:.1f}s)",
                    (w - 180, 42),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA
                )

            with self.live_frame_lock:
                self.latest_live_frame = display_bgr
                self.latest_live_results = results
                self.latest_live_pred = live_pred

    def _live_recognition_loop(self):
        if not self.is_live_rec_mode or not self.camera.is_opened():
            return

        display_bgr = None
        results = None
        live_pred = None
        with self.live_frame_lock:
            if self.latest_live_frame is not None:
                display_bgr = self.latest_live_frame
                results = self.latest_live_results
                live_pred = self.latest_live_pred

        if display_bgr is not None:
            # 1. Hiển thị khung hình lên Canvas
            self._render_frame_on_canvas(display_bgr)

            # 2. Cập nhật nhãn và bảng điều khiển (Throttle mỗi 2-3 ticks)
            self.ui_update_counter += 1
            if self.ui_update_counter % 2 == 0:
                fps = self.camera.get_fps()
                r_detected = results.right_hand_landmarks is not None if results else False
                l_detected = results.left_hand_landmarks is not None if results else False
                p_detected = results.pose_landmarks is not None if results else False
                f_detected = results.face_landmarks is not None if results else False

                # Giữ nhãn ổn định (tránh nhấp nháy chuyển giữa THEO DÕI và 🎯 KÝ TỰ)
                if live_pred and not live_pred.get("in_motion") and live_pred["confidence"] >= 30.0:
                    self.last_stable_pred = live_pred
                    self.stable_pred_hold_count = 25 if live_pred.get("type") == "ĐỘNG" else 8
                elif self.stable_pred_hold_count > 0:
                    self.stable_pred_hold_count -= 1

                active_pred = self.last_stable_pred if self.stable_pred_hold_count > 0 else live_pred

                if active_pred and active_pred.get("in_motion"):
                    self.right_panel.lbl_rec_main.configure(
                        text="💫 [ĐỘNG] ĐANG THỰC HIỆN...",
                        text_color="#FBBF24"
                    )
                    self.right_panel.lbl_rec_confidence.configure(
                        text="Đang nhận diện chuỗi động học (Lắc / Chuyển động)..."
                    )
                    self.right_panel.lbl_rec_details.configure(
                        text=f"Trạng thái: Kinematic Active  |  FPS: {fps}"
                    )
                elif active_pred and active_pred["confidence"] >= 30.0:
                    pred_name = active_pred["name"].upper()
                    conf = active_pred["confidence"]
                    dist = active_pred["distance"]
                    hand_side = active_pred.get("hand", "Right")
                    g_type = active_pred.get("type", "TĨNH")
                    type_icon = "💫" if g_type == "ĐỘNG" else "🖐️"

                    self.right_panel.lbl_rec_main.configure(
                        text=f"🎯 {type_icon} [{g_type}] {pred_name} ({conf}%)",
                        text_color="#00FFCC" if conf >= 60.0 else "#FBBF24"
                    )
                    self.right_panel.lbl_rec_confidence.configure(
                        text=f"Độ tin cậy: {conf}%  |  Sai số: {dist}  |  Loại: {g_type}"
                    )
                    self.right_panel.lbl_rec_details.configure(
                        text=f"Tay: {hand_side}  |  FPS: {fps}  |  Engine: {g_type}"
                    )

                    candidates = active_pred.get("candidates", [])
                    if len(candidates) > 0:
                        self.right_panel.lbl_candidate_1.configure(
                            text=f"1. {candidates[0]['name']} ({candidates[0]['confidence']}%)"
                        )
                    if len(candidates) > 1:
                        self.right_panel.lbl_candidate_2.configure(
                            text=f"2. {candidates[1]['name']} ({candidates[1]['confidence']}%)"
                        )
                    if len(candidates) > 2:
                        self.right_panel.lbl_candidate_3.configure(
                            text=f"3. {candidates[2]['name']} ({candidates[2]['confidence']}%)"
                        )

                elif r_detected or l_detected:
                    hands_txt = []
                    if r_detected: hands_txt.append("Tay Phải [Cyan]")
                    if l_detected: hands_txt.append("Tay Trái [Pink]")
                    hands_str = " + ".join(hands_txt)

                    self.right_panel.lbl_rec_main.configure(text=f"THEO DÕI: {hands_str}", text_color="#A78BFA")
                    self.right_panel.lbl_rec_confidence.configure(text=f"Tốc độ: {fps} FPS | Đang so khớp...")
                    self.right_panel.lbl_rec_details.configure(
                        text=f"Pose: {'[OK]' if p_detected else '[--]'} | Face: {'[OK]' if f_detected else '[--]'}"
                    )
                else:
                    self.right_panel.lbl_rec_main.configure(text="ĐANG TÌM BÀN TAY...", text_color="#F59E0B")
                    self.right_panel.lbl_rec_confidence.configure(text=f"Tốc độ: {fps} FPS | Đưa tay vào khung hình")

        self.after(10, self._live_recognition_loop)

    # ==================== WEBCAM RECORDING MODE ====================

    def toggle_webcam_mode(self):
        if self.is_webcam_mode:
            self.close_webcam()
        else:
            self.open_webcam()

    def open_webcam(self):
        if self.is_live_rec_mode:
            self.close_live_recognition()

        self.open_live_recognition()
        self.is_webcam_mode = True

        self.canvas_panel.live_rec_ctrl_frame.pack_forget()
        self.canvas_panel.webcam_ctrl_frame.pack(fill="x")
        self.canvas_panel.btn_webcam_rec.configure(
            text="🔴 Bắt Đầu Ghi", state="normal", fg_color="#DC2626", hover_color="#B91C1C"
        )
        self.canvas_panel.btn_webcam_stop.configure(
            state="disabled", fg_color="gray30"
        )
        self.canvas_panel.lbl_rec_status.configure(
            text="Sẵn sàng. Nhấn 'Bắt Đầu Ghi' để quay mẫu.", text_color="#38BDF8"
        )
        cam_btn = getattr(self, "left_panel", None) and getattr(self.left_panel, "btn_open_webcam", None) or getattr(self.top_bar, "btn_open_webcam", None)
        if cam_btn:
            cam_btn.configure(text="⏹ Đóng Webcam", fg_color="#DC2626", hover_color="#B91C1C")
        live_btn = getattr(self, "left_panel", None) and getattr(self.left_panel, "btn_live_rec", None) or getattr(self.top_bar, "btn_live_rec", None)
        if live_btn:
            live_btn.configure(text="🎥 Nhận Diện Trực Tiếp", fg_color="#7C3AED", hover_color="#6D28D9")
        print("[Webcam]: Đã mở chế độ quay mẫu Webcam!")

    def close_webcam(self):
        if self.countdown_timer_id is not None:
            self.after_cancel(self.countdown_timer_id)
            self.countdown_timer_id = None
        self.is_recording_sample = False
        self.countdown_val = 0

        self.is_webcam_mode = False
        self.canvas_panel.webcam_ctrl_frame.pack_forget()
        cam_btn = getattr(self, "left_panel", None) and getattr(self.left_panel, "btn_open_webcam", None) or getattr(self.top_bar, "btn_open_webcam", None)
        if cam_btn:
            cam_btn.configure(text="📷 Quay Mẫu Webcam", fg_color="#DB2777", hover_color="#BE185D")
        self.close_live_recognition()
        print("[Webcam]: Đã đóng Webcam.")

    def start_webcam_countdown(self):
        if self.is_recording_sample:
            return
        self.canvas_panel.btn_webcam_rec.configure(state="disabled", text="⏳ Đang đếm ngược...")
        self.canvas_panel.btn_webcam_stop.configure(state="normal", fg_color="#D97706")
        self.countdown_val = 3
        self._countdown_tick()

    def _countdown_tick(self):
        if self.countdown_val > 0:
            self.canvas_panel.lbl_rec_status.configure(
                text=f"⏳ CHUẨN BỊ: {self.countdown_val}... Chuẩn bị đưa tay vào khung hình",
                text_color="#F59E0B"
            )
            self.countdown_val -= 1
            self.countdown_timer_id = self.after(1000, self._countdown_tick)
        else:
            self.countdown_timer_id = None
            self._start_actual_recording()

    def _start_actual_recording(self):
        self.is_recording_sample = True
        self.recorded_frames = []
        self.recorded_keypoints = []

        self.canvas_panel.btn_webcam_rec.configure(
            text="⏺ Đang Ghi Mẫu...", fg_color="#991B1B", state="disabled"
        )
        self.canvas_panel.btn_webcam_stop.configure(
            text="⏹️ Dừng & Sang Biên Tập", fg_color="#10B981", hover_color="#059669", state="normal"
        )
        self.canvas_panel.lbl_rec_status.configure(
            text="🔴 ĐANG GHI MẪU (Bấm 'Dừng' khi hoàn thành)...", text_color="#EF4444"
        )
        print("[Webcam Rec]: Bắt đầu ghi nhận frames sạch vào bộ nhớ tạm...")

    def stop_webcam_recording(self):
        if self.countdown_timer_id is not None:
            self.after_cancel(self.countdown_timer_id)
            self.countdown_timer_id = None

        was_recording = self.is_recording_sample
        self.is_recording_sample = False

        if not was_recording or len(self.recorded_frames) < 5:
            messagebox.showwarning("Thông báo", "Chưa có mẫu nào được ghi (hoặc thời lượng quá ngắn dưới 5 frames)!")
            self.canvas_panel.btn_webcam_rec.configure(
                text="🔴 Bắt Đầu Ghi", state="normal", fg_color="#D03B3B"
            )
            self.canvas_panel.btn_webcam_stop.configure(state="disabled", fg_color="gray30")
            self.canvas_panel.lbl_rec_status.configure(
                text="Sẵn sàng. Nhấn 'Bắt Đầu Ghi' để quay mẫu.", text_color="#38BDF8"
            )
            return

        # Chuyển dữ liệu đã quay vào giao diện biên tập Timeline
        frames = list(self.recorded_frames)
        keypoints = np.array(self.recorded_keypoints, dtype=np.float32)

        # Đóng webcam
        self.close_webcam()

        # Nạp vào hệ thống biên tập
        self.video_frames = frames
        self.video_keypoints = keypoints
        self.fps = 30.0
        self.total_frames = len(frames)
        self.start_frame = 0
        self.end_frame = self.total_frames
        self.curr_frame_idx = 0
        self.is_mirrored_source = True

        # Cấu hình Timeline slider
        self.canvas_panel.timeline_slider.configure(from_=0, to=max(0, self.total_frames - 1))
        self.canvas_panel.timeline_slider.set(0)
        self.update_trim_info()

        # Hiển thị frame đầu tiên
        self._display_current_video_frame()

        # Tự động phân tích chuyển động để gợi ý cấu hình thành phần lưu
        motion_info = detect_gesture_motion(keypoints)
        if motion_info["suggest_arm"]:
            self.right_panel.chk_save_arm.select()
            self.right_panel.chk_save_head.deselect()
            self.right_panel.lbl_save_hint.configure(
                text=f"💡 Phát hiện cử chỉ ĐỘNG (cổ tay dịch chuyển {motion_info['wrist_motion']*100:.1f}%).\nĐã tự động chọn kèm Cánh tay."
            )
        else:
            self.right_panel.chk_save_arm.deselect()
            self.right_panel.chk_save_head.deselect()
            self.right_panel.lbl_save_hint.configure(
                text="💡 Phát hiện cử chỉ TĨNH (cổ tay đứng yên).\nChỉ lưu Bàn tay để triệt tiêu nhiễu khi nhận diện."
            )

        self.top_bar.lbl_file_path.configure(
            text=f"Mẫu Webcam: {self.total_frames} frames (Sẵn sàng biên tập)"
        )

        msg = (
            f"🎬 Đã nạp mẫu cử chỉ vào giao diện biên tập Timeline!\n\n"
            f"• Số khung hình đã quay: {self.total_frames} frames (~{self.total_frames/30.0:.1f}s)\n"
            f"• Các khung hình sạch đã sẵn sàng (chưa lưu đĩa, không dính khung xương).\n\n"
            f"👉 Các bước tiếp theo:\n"
            f"1. Kéo thanh Timeline để xem lại từng khung hình.\n"
            f"2. Bấm [Đặt Bắt Đầu] và [Đặt Kết Thúc] để cắt đoạn cử chỉ chuẩn nhất.\n"
            f"3. Nhập Tên cử chỉ ở ô trên cùng và bấm 'LƯU CỬ CHỈ' -> Hệ thống sẽ xuất Video sạch (.mp4) cùng dữ liệu (.npy & .json)!"
        )
        messagebox.showinfo("Chuyển Sang Biên Tập", msg)
