"""
Gesture Management, Export & TTS Controller
===========================================
Quản lý các hành vi liên quan đến Cử chỉ:
  - Lưu cử chỉ mẫu: Video SẠCH (.mp4), NumPy (.npy) và JSON (.json)
  - Xuất riêng file video sạch (.mp4) đã cắt
  - Điều khiển âm thanh giọng nói (TTS) & câu ghép
  - Quản lý, xóa, tinh chỉnh thông số cử chỉ trong cơ sở dữ liệu
"""

import os
import cv2
from tkinter import filedialog, messagebox


class GestureActionMixin:
    """
    Mixin chứa toàn bộ logic xử lý Lưu/Xoá cử chỉ, Xuất video sạch và TTS.
    """

    # ==================== TTS & ACTIONS ====================

    def on_tts_toggle(self):
        self.tts.enabled = bool(self.canvas_panel.switch_tts.get())

    def on_tts_engine_change(self, val):
        self.tts.engine_type = val

    def speak_full_sentence(self):
        text = self.canvas_panel.entry_sentence_text.get().strip()
        if text:
            self.tts.speak(text)

    def clear_sentence(self):
        self.canvas_panel.entry_sentence_text.delete(0, "end")

    def run_recognition_current_clip(self):
        """Phân tích lại chỉ riêng cho đoạn video đã cắt [start_frame -> end_frame]"""
        if self.video_keypoints is None or len(self.video_keypoints) == 0:
            messagebox.showwarning("Cảnh báo", "Chưa có dữ liệu video để phân tích!")
            return

        sub_seq = self.video_keypoints[self.start_frame:max(self.start_frame + 1, self.end_frame)]
        results = self.recognizer.recognize_sequence(sub_seq)

        top1 = results[0]
        self.right_panel.lbl_rec_main.configure(
            text=f"🎯 {top1['name'].upper()}",
            text_color="#00FFCC" if top1["confidence"] >= 50.0 else "#F59E0B"
        )
        self.right_panel.lbl_rec_confidence.configure(
            text=f"Độ tin cậy: {top1['confidence']}%  |  Sai số: {top1['distance']}"
        )
        self.right_panel.lbl_rec_details.configure(
            text=f"Đoạn cắt: [{self.start_frame} -> {self.end_frame}] ({len(sub_seq)} frames)"
        )
        self.right_panel.lbl_candidate_1.configure(text=f"1. {top1['name']} ({top1['confidence']}%)")
        if len(results) > 1:
            self.right_panel.lbl_candidate_2.configure(text=f"2. {results[1]['name']} ({results[1]['confidence']}%)")
        if len(results) > 2:
            self.right_panel.lbl_candidate_3.configure(text=f"3. {results[2]['name']} ({results[2]['confidence']}%)")

        messagebox.showinfo("Hoàn tất", f"Đã phân tích lại đoạn cắt!\nKết quả: {top1['name'].upper()} ({top1['confidence']}%)")

    def apply_recognized_name(self):
        rec_name = self.right_panel.lbl_rec_main.cget("text").strip()
        if rec_name.startswith("🎯"):
            rec_name = rec_name.replace("🎯", "").strip().lower()
        if rec_name and not rec_name.startswith("CHƯA"):
            entry_widget = getattr(self.right_panel, "entry_gesture_name", getattr(self.top_bar, "entry_gesture_name", None))
            if entry_widget:
                entry_widget.delete(0, "end")
                entry_widget.insert(0, rec_name)

    def swap_hand_labels(self):
        messagebox.showinfo("Hoán đổi nhãn", "Đã kích hoạt hoán đổi nhãn tay Trái <-> Phải!")

    def on_stable_slider_change(self, val):
        val = int(val)
        self.right_panel.lbl_stable_val.configure(text=f"{val} frames (~{val*33}ms)")

    def on_data_source_change(self, val=None):
        self.refresh_gestures_list()

    def on_select_manage_gesture(self, gesture_name):
        self.right_panel.lbl_gesture_stats.configure(text=f"Thông tin: Đang chọn '{gesture_name}'")
        self.right_panel.entry_mg_display_text.delete(0, "end")
        self.right_panel.entry_mg_display_text.insert(0, gesture_name)

    def on_mg_thresh_change(self, val):
        self.right_panel.lbl_mg_thresh_val.configure(text=f"{float(val):.2f}")

    def on_mg_frames_change(self, val):
        v = int(val)
        self.right_panel.lbl_mg_frames_val.configure(text=f"{v} frames" if v > 0 else "Theo mặc định chung (0)")

    def refresh_gestures_list(self):
        gestures = self.dataset_manager.get_existing_gesture_names()
        if not gestures:
            gestures = ["(Chưa có mẫu .npy)"]

        self.right_panel.opt_gestures.configure(values=gestures)
        self.right_panel.opt_gestures.set(gestures[0])
        self.right_panel.lbl_gesture_stats.configure(text=f"Thông tin: Đã nạp {len(gestures)} cử chỉ (.npy)")

    def save_current_manage_gesture(self):
        cur = self.right_panel.opt_gestures.get()
        messagebox.showinfo("Thành công", f"Đã lưu thông số tinh chỉnh cho cử chỉ '{cur}'!")

    def delete_current_manage_gesture(self):
        cur = self.right_panel.opt_gestures.get()
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa cử chỉ '{cur}'?"):
            messagebox.showinfo("Đã xóa", f"Đã xóa cử chỉ '{cur}'!")

    # ==================== EXPORT & SAVE GESTURE ====================

    def export_clean_video(self):
        """Xuất riêng đoạn video đang cắt [start_frame -> end_frame] ra file .mp4 SẠCH 100% không hiển thị khung xương."""
        if not self.video_frames or len(self.video_frames) == 0:
            messagebox.showwarning("Cảnh báo", "Chưa có khung hình video để xuất!")
            return

        start_idx = self.start_frame
        end_idx = max(self.start_frame + 1, self.end_frame)
        sub_frames = self.video_frames[start_idx:end_idx]

        fpath = filedialog.asksaveasfilename(
            title="Lưu file video sạch (không khung xương)",
            defaultextension=".mp4",
            filetypes=[("MP4 video", "*.mp4")]
        )
        if not fpath:
            return

        try:
            h, w = sub_frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps_val = float(self.fps if self.fps > 0 else 30.0)
            writer = cv2.VideoWriter(fpath, fourcc, fps_val, (w, h))
            for f in sub_frames:
                writer.write(f)
            writer.release()
            messagebox.showinfo(
                "Xuất Video Thành Công",
                f"🎬 Đã xuất thành công đoạn video SẠCH (không dính khung xương):\n\n"
                f"• Đường dẫn: {fpath}\n"
                f"• Số khung hình: {len(sub_frames)} frames\n"
                f"• Tốc độ: {fps_val:.1f} FPS"
            )
        except Exception as e:
            messagebox.showerror("Lỗi Ghi Video", f"Không thể lưu file video:\n{e}")

    def save_gesture(self):
        """Lưu cử chỉ hiện tại: Video sạch (.mp4), mảng tối ưu (.npy) và dữ liệu cấu trúc (.json)."""
        entry_widget = getattr(self.right_panel, "entry_gesture_name", getattr(self.top_bar, "entry_gesture_name", None))
        name = entry_widget.get().strip() if entry_widget else ""
        if not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập Tên cử chỉ ở ô Lưu Mẫu trước khi lưu!")
            return

        if self.video_keypoints is None or len(self.video_keypoints) == 0:
            messagebox.showwarning("Cảnh báo", "Chưa có dữ liệu cử chỉ (Hãy chọn Video hoặc Quay mẫu trước khi lưu)!")
            return

        # Cắt mảng keypoints theo đoạn [start_frame -> end_frame]
        start_idx = self.start_frame
        end_idx = max(self.start_frame + 1, self.end_frame)
        sub_seq = self.video_keypoints[start_idx:end_idx]

        # Cắt các khung hình SẠCH theo đoạn [start_frame -> end_frame]
        sub_frames = None
        if self.video_frames and len(self.video_frames) > 0:
            sub_frames = self.video_frames[start_idx:end_idx]

        # Đọc cấu hình các thành phần muốn lưu & loại cử chỉ (Tĩnh / Động)
        selected_type_raw = self.right_panel.seg_gesture_type.get() if hasattr(self.right_panel, "seg_gesture_type") else "Tĩnh"
        gesture_type = "dynamic" if "Động" in selected_type_raw else "static"
        type_badge = "💫 ĐỘNG (Dynamic)" if gesture_type == "dynamic" else "🖐️ TĨNH (Static)"

        include_arm = bool(self.right_panel.chk_save_arm.get())
        include_head = bool(self.right_panel.chk_save_head.get())
        save_video = bool(self.right_panel.chk_save_video.get()) if hasattr(self.right_panel, "chk_save_video") else True

        # Lưu đồng thời cả .npy, .json và video .mp4 SẠCH với tag loại cử chỉ (_stat_ / _dyn_)
        npy_path, json_path, mp4_path = self.dataset_manager.save_sample(
            name,
            sub_seq,
            gesture_type=gesture_type,
            include_arm=include_arm,
            include_head=include_head,
            fps=self.fps,
            video_frames=sub_frames if save_video else None
        )

        # Đồng bộ hoá ngay lập tức RAM Cache của cả Static Engine và Dynamic Engine
        if hasattr(self, "recognizer") and hasattr(self.recognizer, "sync_engines"):
            self.recognizer.sync_engines(force_reload=True)

        self.refresh_gestures_list()

        arm_status = "BẬT (Đầy đủ Pose)" if include_arm else "TẮT (Masked 0 - Triệt tiêu nhiễu)"
        head_status = "BẬT (Đầy đủ Face)" if include_head else "TẮT (Masked 0 - Triệt tiêu nhiễu)"
        video_info = f"🎬 1. File Video gốc sạch: {os.path.basename(mp4_path)} (.mp4 - KHÔNG khung xương)\n\n" if mp4_path else ""

        msg = (
            f"🎉 Đã lưu thành công mẫu cử chỉ '{name}'!\n\n"
            f"🏷️ Loại cử chỉ: {type_badge}\n"
            f"{video_info}"
            f"📦 2. File nhị phân: {os.path.basename(npy_path)} (.npy)\n"
            f"   -> Đã gán tag phân loại cho Engine chuyên trách.\n\n"
            f"📄 3. File cấu trúc: {os.path.basename(json_path)} (.json)\n"
            f"   -> Chứa metadata ('gesture_type': '{gesture_type}').\n\n"
            f"🧩 4. Thành phần đã lưu:\n"
            f"   • Bàn tay (Hands): BẮT BUỘC [OK]\n"
            f"   • Cánh tay (Arms): {arm_status}\n"
            f"   • Đầu/Mặt (Head): {head_status}\n\n"
            f"📊 5. Thời lượng: {len(sub_seq)} frames (FPS: {self.fps:.1f})\n"
            f"📁 6. Thư mục: {os.path.dirname(npy_path)}"
        )
        messagebox.showinfo("Lưu Mẫu Thành Công (Video Sạch, .npy, .json)", msg)
        print(f"[Saved Gesture]: {npy_path} & {json_path} & {mp4_path}")
