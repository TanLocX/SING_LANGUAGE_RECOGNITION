import customtkinter as ctk

class VideoCanvasFrame(ctk.CTkFrame):
    """
    Khu Vực Làm Việc Trung Tâm (Center Workspace):
    - 1. Màn hình Canvas Video / Camera chính
    - 2. Thanh thông báo trạng thái Live / Webcam động
    - 3. Thanh trượt Timeline & Bộ điều khiển playback
    - 4. Khung Phụ đề & Ghép câu Text-to-Speech (TTS)
    """
    def __init__(self, master, callbacks=None, **kwargs):
        super().__init__(
            master, corner_radius=12, fg_color="#0F172A",
            border_width=1, border_color="#1E293B", **kwargs
        )
        self.callbacks = callbacks or {}
        self._build_ui()

    def _build_ui(self):
        # ==================== 1. VIDEO CANVAS ====================
        self.canvas_container = ctk.CTkFrame(self, fg_color="#050811", corner_radius=10, border_width=1, border_color="#1E293B")
        self.canvas_container.pack(fill="both", expand=True, padx=10, pady=(10, 6))

        self.lbl_video_canvas = ctk.CTkLabel(
            self.canvas_container, text="[Màn hình Hiển thị Video / Camera]",
            font=("Segoe UI", 14), text_color="gray50"
        )
        self.lbl_video_canvas.pack(fill="both", expand=True)

        # ==================== 2. STATUS DOCK (LIVE / WEBCAM REC) ====================
        # Container cố định nằm giữa Canvas và Timeline, không bị xung đột pack
        self.status_dock = ctk.CTkFrame(self, fg_color="transparent")
        self.status_dock.pack(fill="x", padx=10, pady=(0, 6))

        # Khung trạng thái Live Rec (Pack động khi bật Live)
        self.live_rec_ctrl_frame = ctk.CTkFrame(self.status_dock, fg_color="#1E1B4B", corner_radius=8, border_width=1, border_color="#4338CA")
        self.lbl_live_status = ctk.CTkLabel(
            self.live_rec_ctrl_frame, text="🔴 ĐANG NHẬN DIỆN TRỰC TIẾP QUA WEBCAM (HOLISTIC)",
            font=("Segoe UI", 12, "bold"), text_color="#A78BFA"
        )
        self.lbl_live_status.pack(side="left", padx=12, pady=6)

        self.btn_live_stop = ctk.CTkButton(
            self.live_rec_ctrl_frame, text="⏹️ Dừng Nhận Diện", width=150, height=32,
            fg_color="#DC2626", hover_color="#B91C1C", font=("Segoe UI", 11, "bold"),
            command=self.callbacks.get("on_close_live")
        )
        self.btn_live_stop.pack(side="right", padx=10, pady=6)

        # Khung trạng thái Quay Mẫu Webcam (Pack động khi quay)
        self.webcam_ctrl_frame = ctk.CTkFrame(self.status_dock, fg_color="#18181B", corner_radius=8, border_width=1, border_color="#27272A")

        self.btn_webcam_rec = ctk.CTkButton(
            self.webcam_ctrl_frame, text="🔴 Bắt Đầu Ghi", width=150, height=34,
            fg_color="#DC2626", hover_color="#B91C1C", font=("Segoe UI", 12, "bold"),
            command=self.callbacks.get("on_start_webcam_rec")
        )
        self.btn_webcam_rec.pack(side="left", padx=10, pady=6)

        self.btn_webcam_stop = ctk.CTkButton(
            self.webcam_ctrl_frame, text="⏹️ Dừng & Chuyển Sang Biên Tập", width=230, height=34,
            fg_color="#059669", hover_color="#047857", font=("Segoe UI", 12, "bold"),
            command=self.callbacks.get("on_stop_webcam_rec")
        )
        self.btn_webcam_stop.pack(side="left", padx=6, pady=6)

        self.lbl_rec_status = ctk.CTkLabel(
            self.webcam_ctrl_frame, text="Sẵn sàng quay mẫu...", font=("Segoe UI", 11, "bold"),
            text_color="#38BDF8"
        )
        self.lbl_rec_status.pack(side="left", padx=10, pady=6)

        self.btn_webcam_close = ctk.CTkButton(
            self.webcam_ctrl_frame, text="❌ Đóng Webcam", width=110, height=34,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 11),
            command=self.callbacks.get("on_close_webcam")
        )
        self.btn_webcam_close.pack(side="right", padx=10, pady=6)

        # ==================== 3. TIMELINE & PLAYBACK CONTROLS ====================
        self.ctrl_card = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.ctrl_card.pack(fill="x", padx=10, pady=(0, 6))

        # Slider row
        self.slider_frame = ctk.CTkFrame(self.ctrl_card, fg_color="transparent")
        self.slider_frame.pack(fill="x", padx=10, pady=(6, 2))

        self.timeline_slider = ctk.CTkSlider(
            self.slider_frame, from_=0, to=100, command=self.callbacks.get("on_slider_moved"),
            height=16, progress_color="#0284C7", button_color="#38BDF8", button_hover_color="#0EA5E9"
        )
        self.timeline_slider.set(0)
        self.timeline_slider.pack(fill="x", side="left", expand=True, padx=(0, 10))

        self.lbl_frame_info = ctk.CTkLabel(
            self.slider_frame, text="Frame: 0 / 0 (0.0s)", font=("Segoe UI", 11, "bold"), width=160, text_color="#38BDF8"
        )
        self.lbl_frame_info.pack(side="right")

        # Playback buttons row
        self.control_buttons_frame = ctk.CTkFrame(self.ctrl_card, fg_color="transparent")
        self.control_buttons_frame.pack(fill="x", padx=10, pady=(2, 8))

        self.btn_step_back5 = ctk.CTkButton(
            self.control_buttons_frame, text="|<< -5f", width=65, height=30,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 10, "bold"),
            command=lambda: self.callbacks.get("on_step_frame", lambda d: None)(-5)
        )
        self.btn_step_back5.pack(side="left", padx=2)

        self.btn_step_back1 = ctk.CTkButton(
            self.control_buttons_frame, text="< -1f", width=60, height=30,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 10, "bold"),
            command=lambda: self.callbacks.get("on_step_frame", lambda d: None)(-1)
        )
        self.btn_step_back1.pack(side="left", padx=2)

        self.btn_play_pause = ctk.CTkButton(
            self.control_buttons_frame, text="▶ Phát Video", width=140, height=32,
            fg_color="#059669", hover_color="#047857", font=("Segoe UI", 12, "bold"),
            command=self.callbacks.get("on_toggle_play")
        )
        self.btn_play_pause.pack(side="left", padx=8)

        self.btn_step_fwd1 = ctk.CTkButton(
            self.control_buttons_frame, text="+1f >", width=60, height=30,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 10, "bold"),
            command=lambda: self.callbacks.get("on_step_frame", lambda d: None)(1)
        )
        self.btn_step_fwd1.pack(side="left", padx=2)

        self.btn_step_fwd5 = ctk.CTkButton(
            self.control_buttons_frame, text="+5f >>", width=65, height=30,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 10, "bold"),
            command=lambda: self.callbacks.get("on_step_frame", lambda d: None)(5)
        )
        self.btn_step_fwd5.pack(side="left", padx=2)

        self.chk_loop = ctk.CTkCheckBox(
            self.control_buttons_frame, text="Lặp đoạn cắt", font=("Segoe UI", 11)
        )
        self.chk_loop.pack(side="left", padx=12)

        # ==================== 4. TTS SUBTITLE BOX ====================
        self.tts_box = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.tts_box.pack(fill="x", padx=10, pady=(0, 10))

        # Top row: Title + Settings
        self.tts_top_row = ctk.CTkFrame(self.tts_box, fg_color="transparent")
        self.tts_top_row.pack(fill="x", padx=10, pady=(8, 2))

        self.lbl_tts_title = ctk.CTkLabel(
            self.tts_top_row, text="🗣️ CÂU THOẠI GHÉP TỪ CỬ CHỈ:", font=("Segoe UI", 11, "bold"), text_color="#38BDF8"
        )
        self.lbl_tts_title.pack(side="left")

        self.switch_tts = ctk.CTkSwitch(
            self.tts_top_row, text="Bật Giọng Nói", font=("Segoe UI", 11, "bold"),
            command=self.callbacks.get("on_tts_toggle")
        )
        self.switch_tts.select()
        self.switch_tts.pack(side="right", padx=(10, 0))

        self.opt_tts_engine = ctk.CTkOptionMenu(
            self.tts_top_row, values=["Google TTS Tiếng Việt", "Offline pyttsx3"],
            font=("Segoe UI", 11), height=26, width=180,
            fg_color="#334155", button_color="#475569",
            command=self.callbacks.get("on_tts_engine_change")
        )
        self.opt_tts_engine.pack(side="right")

        # Sentence Text Entry
        self.entry_sentence_text = ctk.CTkEntry(
            self.tts_box, font=("Segoe UI", 13, "bold"), text_color="#FDE047", fg_color="#0F172A",
            border_color="#38BDF8", height=36,
            placeholder_text="Câu thoại tự động ghép từ cử chỉ nhận diện..."
        )
        self.entry_sentence_text.pack(fill="x", padx=10, pady=(2, 6))

        # Sentence Actions
        self.tts_btn_row = ctk.CTkFrame(self.tts_box, fg_color="transparent")
        self.tts_btn_row.pack(fill="x", padx=10, pady=(0, 8))

        self.btn_speak_sentence = ctk.CTkButton(
            self.tts_btn_row, text="🔊 Đọc Cả Câu", width=120, height=28,
            fg_color="#059669", hover_color="#047857", font=("Segoe UI", 11, "bold"),
            command=self.callbacks.get("on_speak_sentence")
        )
        self.btn_speak_sentence.pack(side="left", padx=(0, 6))

        self.btn_clear_sentence = ctk.CTkButton(
            self.tts_btn_row, text="🗑️ Xóa Câu", width=90, height=28,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 11),
            command=self.callbacks.get("on_clear_sentence")
        )
        self.btn_clear_sentence.pack(side="left")

        self.switch_prevent_dup = ctk.CTkSwitch(
            self.tts_btn_row, text="🚫 Không lặp từ liên tiếp", font=("Segoe UI", 11),
            text_color="#A78BFA"
        )
        self.switch_prevent_dup.select()
        self.switch_prevent_dup.pack(side="left", padx=(14, 0))
