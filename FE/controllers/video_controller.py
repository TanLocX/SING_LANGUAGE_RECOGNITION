"""
Video Playback & Timeline Editing Controller
============================================
Quản lý luồng hoạt động của Video file và Trình biên tập Timeline:
  - Chọn và quét video file để nhận diện
  - Nạp video vào trình biên tập
  - Điều khiển playback: Play/Pause, tua từng frame, slider timeline
  - Đặt điểm cắt Bắt Đầu / Kết Thúc
  - Hiển thị khung hình sạch lên Canvas kèm khung xương động (dynamic overlay)
"""

import os
import threading
import cv2
import numpy as np
from PIL import Image
from tkinter import filedialog, messagebox
import customtkinter as ctk

from BE import (
    draw_keypoints_vector,
    detect_gesture_motion,
    normalize_hand_landmarks,
    extract_active_hand_shape,
)


class VideoPlayerMixin:
    """
    Mixin chứa toàn bộ logic xử lý Video, Timeline playback và Canvas rendering.
    """

    def choose_video_for_recognition(self):
        if self.is_scanning:
            messagebox.showwarning("Cảnh báo", "Đang trong tiến trình quét video, vui lòng đợi!")
            return

        fpath = filedialog.askopenfilename(
            title="Chọn video để nhận diện cử chỉ (.npy)",
            filetypes=[("Video files", "*.mp4 *.mov *.avi *.webm *.mkv")]
        )
        if not fpath:
            return

        # Dừng camera nếu đang live
        if self.is_live_rec_mode:
            self.close_live_recognition()

        self.video_path = fpath
        self.top_bar.lbl_file_path.configure(text=f"Đang nhận diện: {os.path.basename(fpath)}")
        self.top_bar.set_progress(0.02, "Khởi tạo quét video...")

        # Chạy quét video và so khớp trong luồng ngầm
        def _scan_thread():
            self.is_scanning = True
            try:
                frames, keypoints, fps = self.recognizer.process_video_file(
                    fpath,
                    progress_callback=lambda cur, tot, pct: self.after(
                        0, lambda: self.top_bar.set_progress(pct / 100.0, f"Đang quét: {cur}/{tot} frames ({pct}%)")
                    )
                )
                self.after(0, lambda: self._on_scan_completed(fpath, frames, keypoints, fps))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Lỗi Quét Video", f"Không thể xử lý video:\n{e}"))
            finally:
                self.is_scanning = False
                self.after(0, lambda: self.top_bar.set_progress(0))

        threading.Thread(target=_scan_thread, daemon=True).start()

    def _on_scan_completed(self, fpath: str, frames: list, keypoints: np.ndarray, fps: float):
        if not frames or keypoints is None or len(keypoints) == 0:
            messagebox.showwarning("Thông báo", "Không trích xuất được khung hình nào từ video!")
            return

        self.video_frames = frames
        self.video_keypoints = keypoints
        self.fps = fps or 30.0
        self.total_frames = len(frames)
        self.start_frame = 0
        self.end_frame = self.total_frames
        self.curr_frame_idx = 0
        self.is_mirrored_source = False

        # Cấu hình Timeline slider
        self.canvas_panel.timeline_slider.configure(from_=0, to=max(0, self.total_frames - 1))
        self.canvas_panel.timeline_slider.set(0)
        self.update_trim_info()

        # Hiển thị frame đầu tiên
        self._display_current_video_frame()

        # Tự động phân tích chuyển động để gợi ý cấu hình thành phần lưu & loại Cử chỉ
        motion_info = detect_gesture_motion(keypoints)
        if motion_info["suggest_arm"]:
            if hasattr(self.right_panel, "seg_gesture_type"):
                self.right_panel.seg_gesture_type.set("💫 Động (Dynamic)")
            self.right_panel.chk_save_arm.select()
            self.right_panel.chk_save_head.deselect()
            self.right_panel.lbl_save_hint.configure(
                text=f"💡 Phát hiện cử chỉ ĐỘNG (cổ tay dịch chuyển {motion_info['wrist_motion']*100:.1f}%).\nĐã tự động chọn kèm Cánh tay."
            )
        else:
            if hasattr(self.right_panel, "seg_gesture_type"):
                self.right_panel.seg_gesture_type.set("🖐️ Tĩnh (Static)")
            self.right_panel.chk_save_arm.deselect()
            self.right_panel.chk_save_head.deselect()
            self.right_panel.lbl_save_hint.configure(
                text="💡 Phát hiện cử chỉ TĨNH (cổ tay đứng yên).\nChỉ lưu Bàn tay để triệt tiêu nhiễu khi nhận diện."
            )

        # Thực hiện so khớp chuỗi keypoints với các template .npy
        results = self.recognizer.recognize_sequence(keypoints)

        top1 = results[0]
        top1_name = top1["name"]
        top1_conf = top1["confidence"]
        top1_dist = top1["distance"]

        # Cập nhật Card nhận diện Section 1
        self.right_panel.lbl_rec_main.configure(
            text=f"🎯 {top1_name.upper()}",
            text_color="#00FFCC" if top1_conf >= 50.0 else "#F59E0B"
        )
        self.right_panel.lbl_rec_confidence.configure(
            text=f"Độ tin cậy: {top1_conf}%  |  Sai số: {top1_dist}"
        )
        self.right_panel.lbl_rec_details.configure(
            text=f"So khớp: {top1['frames']} frames (.npy) | Video gốc: {self.total_frames} frames"
        )

        # Cập nhật Top 3 candidates
        c1_text = f"1. {top1_name} ({top1_conf}%)"
        self.right_panel.lbl_candidate_1.configure(text=c1_text)

        c2_text = f"2. {results[1]['name']} ({results[1]['confidence']}%)" if len(results) > 1 else "2. ---"
        self.right_panel.lbl_candidate_2.configure(text=c2_text)

        c3_text = f"3. {results[2]['name']} ({results[2]['confidence']}%)" if len(results) > 2 else "3. ---"
        self.right_panel.lbl_candidate_3.configure(text=c3_text)

        # Gán tự động vào ô tên cử chỉ để tiện lưu mẫu
        self.top_bar.entry_gesture_name.delete(0, "end")
        self.top_bar.entry_gesture_name.insert(0, top1_name)

        # Cập nhật vào câu thoại và phát âm nếu bật
        if top1_name and not top1_name.startswith("("):
            prev_sentence = self.canvas_panel.entry_sentence_text.get().strip()
            # Kiểm tra chống lặp từ nếu bật switch
            prevent_dup = bool(self.canvas_panel.switch_prevent_dup.get())
            words = prev_sentence.split()
            if not prevent_dup or (not words or words[-1].lower() != top1_name.lower()):
                new_sentence = f"{prev_sentence} {top1_name}".strip()
                self.canvas_panel.entry_sentence_text.delete(0, "end")
                self.canvas_panel.entry_sentence_text.insert(0, new_sentence)

                # Phát âm nếu bật giọng nói
                if self.canvas_panel.switch_tts.get():
                    self.tts.speak(top1_name)

        self.top_bar.lbl_file_path.configure(text=f"Đã nhận diện: {os.path.basename(fpath)} -> [{top1_name.upper()}]")
        print(f"[Video Recognized]: {top1_name} ({top1_conf}%) from {fpath}")

    # ==================== VIDEO PLAYBACK & TIMELINE CONTROLS ====================

    def choose_video(self):
        fpath = filedialog.askopenfilename(
            title="Chọn video biên tập",
            filetypes=[("Video files", "*.mp4 *.mov *.avi *.webm *.mkv")]
        )
        if not fpath:
            return

        if self.is_live_rec_mode:
            self.close_live_recognition()

        self.video_path = fpath
        self.top_bar.lbl_file_path.configure(text=f"Biên tập: {os.path.basename(fpath)}")
        self.top_bar.set_progress(0.05, "Đang nạp video...")

        def _load_thread():
            self.is_scanning = True
            try:
                frames, keypoints, fps = self.recognizer.process_video_file(
                    fpath,
                    progress_callback=lambda cur, tot, pct: self.after(
                        0, lambda: self.top_bar.set_progress(pct / 100.0, f"Đang nạp: {cur}/{tot} frames ({pct}%)")
                    )
                )
                self.after(0, lambda: self._on_video_loaded(fpath, frames, keypoints, fps))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Lỗi Mở Video", str(e)))
            finally:
                self.is_scanning = False
                self.after(0, lambda: self.top_bar.set_progress(0))

        threading.Thread(target=_load_thread, daemon=True).start()

    def _on_video_loaded(self, fpath: str, frames: list, keypoints: np.ndarray, fps: float):
        if not frames:
            messagebox.showwarning("Thông báo", "Không mở được video!")
            return

        self.video_frames = frames
        self.video_keypoints = keypoints
        self.fps = fps or 30.0
        self.total_frames = len(frames)
        self.start_frame = 0
        self.end_frame = self.total_frames
        self.curr_frame_idx = 0
        self.is_mirrored_source = False

        self.canvas_panel.timeline_slider.configure(from_=0, to=max(0, self.total_frames - 1))
        self.canvas_panel.timeline_slider.set(0)
        self.update_trim_info()
        self._display_current_video_frame()

        # Tự động nhận diện cho video vừa nạp
        if keypoints is not None and len(keypoints) > 0:
            results = self.recognizer.recognize_sequence(keypoints)
            top1 = results[0]
            self.right_panel.lbl_rec_main.configure(
                text=f"🎯 {top1['name'].upper()}",
                text_color="#00FFCC" if top1["confidence"] >= 50.0 else "#FBBF24"
            )
            self.right_panel.lbl_rec_confidence.configure(
                text=f"Độ tin cậy: {top1['confidence']}%  |  Sai số: {top1['distance']}"
            )
            self.right_panel.lbl_candidate_1.configure(text=f"1. {top1['name']} ({top1['confidence']}%)")
            self.top_bar.entry_gesture_name.delete(0, "end")
            self.top_bar.entry_gesture_name.insert(0, top1['name'])

    def _display_current_video_frame(self):
        if not self.video_frames or self.curr_frame_idx >= len(self.video_frames):
            return
        # Tạo bản sao từ khung hình SẠCH (khung hình gốc self.video_frames không bao giờ bị ghi đè)
        frame = self.video_frames[self.curr_frame_idx].copy()

        # 1. Vẽ khung xương động trên bản sao hiển thị (nếu người dùng bật checkbox tương ứng)
        if self.video_keypoints is not None and self.curr_frame_idx < len(self.video_keypoints):
            curr_kp = self.video_keypoints[self.curr_frame_idx]
            opt_panel = getattr(self, "left_panel", self.right_panel)
            show_hands = bool(opt_panel.chk_landmarks.get())
            show_pose = bool(opt_panel.chk_arm_pose.get())
            show_face = bool(opt_panel.chk_head_tracker.get())

            frame = draw_keypoints_vector(
                frame,
                curr_kp,
                show_hands=show_hands,
                show_pose=show_pose,
                show_face=show_face,
                mirror=getattr(self, "is_mirrored_source", True)
            )

            # 2. Nhận diện bàn tay ngay tại frame hiện tại trên timeline (nếu bật chk_rec_hud)
            if opt_panel.chk_rec_hud.get():
                rh = curr_kp[1599:1662].reshape(21, 3)
                lh = curr_kp[1536:1599].reshape(21, 3)
                hand_arr = rh if not np.all(rh == 0) else (lh if not np.all(lh == 0) else None)
                if hand_arr is not None:
                    norm_hand = normalize_hand_landmarks(hand_arr)
                    templates = self.dataset_manager.load_all_templates()
                    best_n, best_d = None, float("inf")
                    for gn, s_list in templates.items():
                        for tpl in s_list:
                            tpl_h, _ = extract_active_hand_shape(tpl)
                            if tpl_h is not None:
                                d = float(np.mean(np.linalg.norm(norm_hand - tpl_h, axis=1)))
                                if d < best_d:
                                    best_d = d
                                    best_n = gn
                    if best_n is not None:
                        cf = max(0.0, min(100.0, (1.0 - best_d / 0.45) * 100.0))
                        if cf >= 35.0:
                            cv2.putText(
                                frame,
                                f"FRAME {self.curr_frame_idx}: [{best_n.upper()}] ({cf:.0f}%)",
                                (20, 45),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                (0, 255, 200),
                                2,
                                cv2.LINE_AA
                            )
                            self.right_panel.lbl_rec_main.configure(
                                text=f"🎯 {best_n.upper()} (Frame {self.curr_frame_idx}: {cf:.0f}%)",
                                text_color="#00FFCC" if cf >= 70.0 else "#FBBF24"
                            )
                            self.right_panel.lbl_rec_confidence.configure(
                                text=f"Độ tin cậy: {cf:.1f}%  |  Sai số: {best_d:.3f}"
                            )

        self._render_frame_on_canvas(frame)
        self.update_trim_info()

    def _render_frame_on_canvas(self, bgr_img: np.ndarray):
        container = self.canvas_panel.canvas_container
        cw = max(400, container.winfo_width() - 16)
        ch = max(300, container.winfo_height() - 16)
        h, w, _ = bgr_img.shape
        aspect = w / h

        if cw / ch > aspect:
            new_h = ch
            new_w = int(new_h * aspect)
        else:
            new_w = cw
            new_h = int(new_w / aspect)

        resized = cv2.resize(bgr_img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        pil_img = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(new_w, new_h))
        self.canvas_panel.lbl_video_canvas.configure(image=ctk_img, text="")
        self.canvas_panel.lbl_video_canvas.image = ctk_img

    def mark_start_frame(self):
        self.start_frame = int(self.canvas_panel.timeline_slider.get())
        if self.start_frame > self.end_frame:
            self.end_frame = self.start_frame
        self.update_trim_info()

    def mark_end_frame(self):
        self.end_frame = int(self.canvas_panel.timeline_slider.get())
        if self.end_frame < self.start_frame:
            self.start_frame = self.end_frame
        self.update_trim_info()

    def reset_trim(self):
        self.start_frame = 0
        self.end_frame = max(0, self.total_frames)
        self.update_trim_info()

    def update_trim_info(self):
        dur_f = max(0, self.end_frame - self.start_frame)
        fps_val = self.fps if self.fps > 0 else 30.0
        dur_s = dur_f / fps_val
        curr_s = self.curr_frame_idx / fps_val
        self.right_panel.lbl_trim_range.configure(text=f"Đoạn cắt: [{self.start_frame} -> {self.end_frame}]")
        self.right_panel.lbl_trim_duration.configure(text=f"Thời lượng: {dur_f} frames ({dur_s:.2f}s)")
        self.canvas_panel.lbl_frame_info.configure(
            text=f"Frame: {self.curr_frame_idx}/{self.total_frames} ({curr_s:.2f}s) | {fps_val:.1f} FPS"
        )

        # Tự động gợi ý loại Cử chỉ (Tĩnh / Động) dựa trên phân tích chuyển động đoạn cắt
        if hasattr(self, "video_keypoints") and self.video_keypoints is not None and len(self.video_keypoints) > 0 and dur_f >= 3:
            sub_seq = self.video_keypoints[self.start_frame:self.end_frame]
            motion_info = detect_gesture_motion(sub_seq)
            if hasattr(self.right_panel, "seg_gesture_type"):
                if motion_info["suggest_arm"]:
                    self.right_panel.seg_gesture_type.set("💫 Động (Dynamic)")
                    if hasattr(self.right_panel, "_on_gesture_type_changed"):
                        self.right_panel._on_gesture_type_changed("💫 Động (Dynamic)")
                else:
                    self.right_panel.seg_gesture_type.set("🖐️ Tĩnh (Static)")
                    if hasattr(self.right_panel, "_on_gesture_type_changed"):
                        self.right_panel._on_gesture_type_changed("🖐️ Tĩnh (Static)")

    def toggle_play(self):
        if not self.video_frames:
            return
        self.is_playing = not self.is_playing
        self.canvas_panel.btn_play_pause.configure(text="⏸ Tạm Dừng" if self.is_playing else "▶ Phát Video")
        if self.is_playing:
            self._play_video_loop()

    def _play_video_loop(self):
        if not self.is_playing or not self.video_frames:
            return

        self.curr_frame_idx += 1
        # Kiểm tra lặp đoạn cắt
        loop_crop = bool(self.canvas_panel.chk_loop.get())
        if loop_crop:
            if self.curr_frame_idx >= self.end_frame:
                self.curr_frame_idx = self.start_frame
        else:
            if self.curr_frame_idx >= len(self.video_frames):
                self.curr_frame_idx = 0

        self.canvas_panel.timeline_slider.set(self.curr_frame_idx)
        self._display_current_video_frame()

        delay_ms = max(10, int(1000 / (self.fps if self.fps > 0 else 30.0)))
        self.after(delay_ms, self._play_video_loop)

    def step_frame(self, delta):
        if not self.video_frames:
            return
        self.curr_frame_idx = max(0, min(self.total_frames - 1, self.curr_frame_idx + delta))
        self.canvas_panel.timeline_slider.set(self.curr_frame_idx)
        self._display_current_video_frame()

    def on_slider_moved(self, val):
        if not self.video_frames:
            return
        self.curr_frame_idx = int(val)
        self._display_current_video_frame()
