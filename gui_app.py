"""
Sign Language Recognition Studio - Modular Controller (Entry Point)
===================================================================
Kiến trúc tách module:
  - Frontend   (FE/): TopBarFrame, VideoCanvasFrame, RightPanelFrame
  - Backend    (BE/): CameraManager, HolisticTracker, TTSManager, 
                      GestureDatasetManager, VideoRecognizer, extract_keypoints
  - Controllers(controllers/): LiveWebcamMixin, VideoPlayerMixin, GestureActionMixin
"""

import sys
import threading
import customtkinter as ctk

# Thiết lập UTF-8 trên Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Import Backend & Frontend
from BE import (
    CameraManager,
    HolisticTracker,
    OnnxTracker,
    TTSManager,
    GestureDatasetManager,
    VideoRecognizer,
)
from FE import (
    TopBarFrame,
    LeftSidebarFrame,
    VideoCanvasFrame,
    RightPanelFrame,
    LiveWebcamMixin,
    VideoPlayerMixin,
    GestureActionMixin,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VideoGestureTrainerApp(ctk.CTk, LiveWebcamMixin, VideoPlayerMixin, GestureActionMixin):
    """
    Ứng dụng chính Sign Language Studio.
    Kế thừa các Mixin chức năng chuyên biệt giúp mã nguồn rõ ràng, dễ bảo trì.
    """
    def __init__(self):
        super().__init__()

        self.title("Sign Language Studio - Holistic Studio Pro")
        self.geometry("1480x880")
        self.minsize(1080, 760)

        # 1. Backend Managers
        self.camera = CameraManager(camera_index=0, target_width=640, target_height=480)
        
        # Hỗ trợ song song cả GPU DirectML (RTX 3050) và CPU MediaPipe Holistic
        self.gpu_tracker = None
        self.cpu_tracker = None
        try:
            self.gpu_tracker = OnnxTracker(use_gpu=True)
            self.tracker = self.gpu_tracker
            print("[Studio Pro]: Tự động kích hoạt GPU NVIDIA GeForce RTX 3050!")
        except Exception as e:
            print(f"[Studio Pro Warning]: Không thể nạp GPU OnnxTracker ({e}), chuyển sang CPU.")
            self.cpu_tracker = HolisticTracker(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            self.tracker = self.cpu_tracker

        self.tts = TTSManager()
        self.dataset_manager = GestureDatasetManager()
        self.recognizer = VideoRecognizer(self.tracker, self.dataset_manager)

        # 2. State Variables
        self.is_live_rec_mode = False
        self.is_webcam_mode = False
        self.is_playing = False
        self.is_scanning = False
        self.is_mirrored_source = True

        self.video_path = ""
        self.video_frames = []
        self.video_keypoints = None
        self.fps = 30.0
        self.total_frames = 0
        self.curr_frame_idx = 0
        self.start_frame = 0
        self.end_frame = 0
        self.ui_update_counter = 0

        # Threaded Live Processing (Đảm bảo 30+ FPS không lag giật)
        self.live_frame_lock = threading.Lock()
        self.latest_live_frame = None
        self.latest_live_results = None
        self.latest_live_pred = None
        self.live_worker_thread = None
        self.last_stable_pred = None
        self.stable_pred_hold_count = 0

        # Webcam Sample Recording
        self.is_recording_sample = False
        self.countdown_val = 0
        self.countdown_timer_id = None
        self.recorded_frames = []
        self.recorded_keypoints = []

        # 3. Setup Layout
        self._init_layout()

        # Nạp danh sách cử chỉ ban đầu
        self.refresh_gestures_list()

    def _init_layout(self):
        # Master container for callback bindings
        callbacks = {
            # Top bar
            "on_engine_change": self.on_engine_change,
            "on_toggle_live": self.toggle_live_recognition_mode,
            "on_rec_video": self.choose_video_for_recognition,
            "on_open_video": self.choose_video,
            "on_toggle_webcam": self.toggle_webcam_mode,
            "on_data_source_change": self.on_data_source_change,

            # Video canvas & TTS
            "on_close_live": self.close_live_recognition,
            "on_start_webcam_rec": self.start_webcam_countdown,
            "on_stop_webcam_rec": self.stop_webcam_recording,
            "on_close_webcam": self.close_webcam,
            "on_tts_toggle": self.on_tts_toggle,
            "on_tts_engine_change": self.on_tts_engine_change,
            "on_speak_sentence": self.speak_full_sentence,
            "on_clear_sentence": self.clear_sentence,
            "on_slider_moved": self.on_slider_moved,
            "on_toggle_play": self.toggle_play,
            "on_step_frame": self.step_frame,

            # Right panel
            "on_run_rec_clip": self.run_recognition_current_clip,
            "on_apply_rec_name": self.apply_recognized_name,
            "on_mark_start": self.mark_start_frame,
            "on_mark_end": self.mark_end_frame,
            "on_reset_trim": self.reset_trim,
            "on_export_video": self.export_clean_video,
            "on_hand_mode_change": lambda v: print(f"[Hand Mode]: {v}"),
            "on_hand_side_override_change": lambda v: print(f"[Hand Side Override]: {v}"),
            "on_swap_hands": self.swap_hand_labels,
            "on_mode_change": lambda v: print(f"[Gesture Mode]: {v}"),
            "on_track_change": lambda v: print(f"[Track Point]: {v}"),
            "on_geom_norm_toggle": lambda: print("[Geom Norm Toggle]"),
            "on_stable_slider_change": self.on_stable_slider_change,
            "on_select_manage_gesture": self.on_select_manage_gesture,
            "on_refresh_gestures": self.refresh_gestures_list,
            "on_mg_thresh_change": self.on_mg_thresh_change,
            "on_mg_frames_change": self.on_mg_frames_change,
            "on_save_mg": self.save_current_manage_gesture,
            "on_delete_mg": self.delete_current_manage_gesture,
            "on_save_gesture": self.save_gesture,
        }

        # Top Bar
        self.top_bar = TopBarFrame(self, callbacks=callbacks)
        self.top_bar.pack(fill="x", padx=15, pady=(12, 6))

        # Main 3-Column Split Content
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.pack(fill="both", expand=True, padx=15, pady=4)

        # Cột 1: Bảng Điều Khiển & CSDL Cử Chỉ (Left Sidebar)
        self.left_panel = LeftSidebarFrame(self.main_content, callbacks=callbacks)
        self.left_panel.pack(side="left", fill="y", padx=(0, 10))

        # Cột 2: Màn Hình Canvas & Phụ Đề TTS (Center Workspace)
        self.canvas_panel = VideoCanvasFrame(self.main_content, callbacks=callbacks)
        self.canvas_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Cột 3: Kết Quả & Lưu Mẫu (Right Inspector Panel)
        self.right_panel = RightPanelFrame(self.main_content, callbacks=callbacks)
        self.right_panel.pack(side="right", fill="y", padx=0)

        # ============================================================
        # Tương thích ngược: Gán alias cho các controllers & handlers cũ
        # ============================================================
        self.top_bar.btn_live_rec = self.left_panel.btn_live_rec
        self.top_bar.btn_open_webcam = self.left_panel.btn_open_webcam
        self.top_bar.btn_rec_video = self.left_panel.btn_rec_video
        self.top_bar.btn_open_video = self.left_panel.btn_open_video
        self.top_bar.entry_gesture_name = self.right_panel.entry_gesture_name

        self.right_panel.chk_landmarks = self.left_panel.chk_landmarks
        self.right_panel.chk_arm_pose = self.left_panel.chk_arm_pose
        self.right_panel.chk_head_tracker = self.left_panel.chk_head_tracker
        self.right_panel.chk_trail = self.left_panel.chk_trail
        self.right_panel.chk_rec_hud = self.left_panel.chk_rec_hud
        self.right_panel.chk_geom_norm = self.left_panel.chk_geom_norm
        self.right_panel.chk_interp = self.left_panel.chk_interp
        self.right_panel.seg_hands = self.left_panel.seg_hands
        self.right_panel.seg_hand_side = self.left_panel.seg_hand_side
        self.right_panel.opt_gestures = self.left_panel.opt_gestures
        self.right_panel.lbl_gesture_stats = self.left_panel.lbl_gesture_stats
        self.right_panel.entry_mg_display_text = self.left_panel.entry_mg_display_text
        self.right_panel.lbl_mg_thresh_val = self.left_panel.lbl_mg_thresh_val
        self.right_panel.lbl_mg_frames_val = self.left_panel.lbl_mg_frames_val
        self.right_panel.slider_mg_thresh = self.left_panel.slider_mg_thresh
        self.right_panel.slider_mg_frames = self.left_panel.slider_mg_frames
        self.right_panel.lbl_stable_val = self.left_panel.lbl_stable_val
        self.right_panel.slider_stable = self.left_panel.slider_stable
        self.right_panel.seg_data_source = self.left_panel.seg_data_source

    def on_engine_change(self, val):
        """Chuyển đổi nóng giữa GPU NVIDIA RTX 3050 và CPU MediaPipe"""
        if "GPU" in val:
            if self.gpu_tracker is None:
                self.gpu_tracker = OnnxTracker(use_gpu=True)
            self.tracker = self.gpu_tracker
            self.recognizer.tracker = self.gpu_tracker
            self.top_bar.lbl_file_path.configure(
                text="⚡ Đang tăng tốc bằng GPU NVIDIA GeForce RTX 3050 (DirectML)!"
            )
            print("[Hardware Engine]: Đã chuyển sang GPU RTX 3050 (DirectML)")
        else:
            if self.cpu_tracker is None:
                self.cpu_tracker = HolisticTracker(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            self.tracker = self.cpu_tracker
            self.recognizer.tracker = self.cpu_tracker
            self.top_bar.lbl_file_path.configure(
                text="💻 Đang xử lý bằng CPU (MediaPipe Holistic tiêu chuẩn)."
            )
            print("[Hardware Engine]: Đã chuyển sang CPU MediaPipe Holistic")

    def on_closing(self):
        self.is_playing = False
        self.is_scanning = False
        self.camera.release()
        if self.gpu_tracker:
            self.gpu_tracker.close()
        if self.cpu_tracker:
            self.cpu_tracker.close()
        self.destroy()


if __name__ == "__main__":
    app = VideoGestureTrainerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
