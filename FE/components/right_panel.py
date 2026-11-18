import customtkinter as ctk

class RightPanelFrame(ctk.CTkScrollableFrame):
    """
    Cột Phải - Bảng Kết Quả & Lưu Mẫu (Right Inspector Panel):
    - Mục 1: Kết quả nhận diện (Hero Card, Độ tin cậy, Top 3 candidates)
    - Mục 2: Cắt gọt đoạn cử chỉ (Đặt bắt đầu, Đặt kết thúc, Thông tin, Xuất video sạch)
    - Mục 3: Lưu mẫu cơ sở dữ liệu (Tên cử chỉ, Thành phần lưu, Nút lưu Master)
    """
    def __init__(self, master, callbacks=None, **kwargs):
        super().__init__(
            master, width=340, corner_radius=12,
            fg_color="#0F172A", border_width=1, border_color="#1E293B",
            **kwargs
        )
        self.callbacks = callbacks or {}
        self._build_ui()

    def _build_ui(self):
        # ==================== MỤC 1: KẾT QUẢ NHẬN DIỆN ====================
        self._build_header("🎯 KẾT QUẢ NHẬN DIỆN", "#10B981")

        self.rec_card = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.rec_card.pack(fill="x", padx=6, pady=(0, 10))

        # Bộ chọn chế độ nhận diện (Recognition Mode Selector)
        self.seg_rec_mode = ctk.CTkSegmentedButton(
            self.rec_card,
            values=["🔄 Tự Động", "🖐️ Tĩnh", "💫 Động"],
            font=("Segoe UI", 11, "bold"),
            selected_color="#059669",
            selected_hover_color="#047857",
            command=self._on_rec_mode_changed
        )
        self.seg_rec_mode.set("🔄 Tự Động")
        self.seg_rec_mode.pack(fill="x", padx=10, pady=(10, 6))

        # Hero result display
        self.lbl_rec_main = ctk.CTkLabel(
            self.rec_card, text="✨ CHƯA CÓ KẾT QUẢ", font=("Segoe UI", 16, "bold"), text_color="#34D399"
        )
        self.lbl_rec_main.pack(anchor="w", padx=12, pady=(10, 2))

        self.lbl_rec_confidence = ctk.CTkLabel(
            self.rec_card, text="Độ tin cậy: --%  |  Sai số: --", font=("Segoe UI", 12, "bold"), text_color="white"
        )
        self.lbl_rec_confidence.pack(anchor="w", padx=12, pady=(0, 2))

        self.lbl_rec_details = ctk.CTkLabel(
            self.rec_card, text="Cấu trúc: --  |  Số frame khớp: --", font=("Segoe UI", 11), text_color="gray75"
        )
        self.lbl_rec_details.pack(anchor="w", padx=12, pady=(0, 8))

        # Top 3 Candidates
        self.candidates_box = ctk.CTkFrame(self.rec_card, fg_color="#0F172A", corner_radius=8)
        self.candidates_box.pack(fill="x", padx=10, pady=(0, 8))

        self.lbl_cand_title = ctk.CTkLabel(
            self.candidates_box, text="Top dự đoán tương đồng:", font=("Segoe UI", 11, "bold"), text_color="gray70"
        )
        self.lbl_cand_title.pack(anchor="w", padx=10, pady=(6, 2))

        self.lbl_candidate_1 = ctk.CTkLabel(self.candidates_box, text="1. ---", font=("Segoe UI", 11), text_color="#34D399")
        self.lbl_candidate_1.pack(anchor="w", padx=10, pady=1)

        self.lbl_candidate_2 = ctk.CTkLabel(self.candidates_box, text="2. ---", font=("Segoe UI", 11), text_color="gray80")
        self.lbl_candidate_2.pack(anchor="w", padx=10, pady=1)

        self.lbl_candidate_3 = ctk.CTkLabel(self.candidates_box, text="3. ---", font=("Segoe UI", 11), text_color="gray80")
        self.lbl_candidate_3.pack(anchor="w", padx=10, pady=(1, 8))

        # Action Buttons
        self.btn_run_rec = ctk.CTkButton(
            self.rec_card, text="⚡ Phân Tích Lại Đoạn Cắt", height=32,
            fg_color="#059669", hover_color="#047857", font=("Segoe UI", 11, "bold"),
            command=self.callbacks.get("on_run_rec_clip")
        )
        self.btn_run_rec.pack(fill="x", padx=10, pady=(0, 4))

        self.btn_apply_name = ctk.CTkButton(
            self.rec_card, text="🏷️ Gán Tên Sang Ô Lưu Mẫu", height=30,
            fg_color="#475569", hover_color="#334155", font=("Segoe UI", 11),
            command=self.callbacks.get("on_apply_rec_name")
        )
        self.btn_apply_name.pack(fill="x", padx=10, pady=(0, 10))

        # ==================== MỤC 2: CẮT ĐOẠN CỬ CHỈ ====================
        self._build_header("✂️ BIÊN TẬP ĐOẠN CẮT", "#38BDF8")

        trim_box = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        trim_box.pack(fill="x", padx=6, pady=(0, 10))

        # Nút Đặt Bắt Đầu & Kết Thúc đặt ngang hàng nhau rất trực quan
        trim_btn_row = ctk.CTkFrame(trim_box, fg_color="transparent")
        trim_btn_row.pack(fill="x", padx=10, pady=(10, 4))

        self.btn_set_start = ctk.CTkButton(
            trim_btn_row, text="🚩 Đặt Bắt Đầu", height=34,
            fg_color="#0284C7", hover_color="#0369A1", font=("Segoe UI", 11, "bold"),
            command=self.callbacks.get("on_mark_start")
        )
        self.btn_set_start.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_set_end = ctk.CTkButton(
            trim_btn_row, text="🏁 Đặt Kết Thúc", height=34,
            fg_color="#D97706", hover_color="#B45309", font=("Segoe UI", 11, "bold"),
            command=self.callbacks.get("on_mark_end")
        )
        self.btn_set_end.pack(side="right", expand=True, fill="x", padx=(4, 0))

        self.btn_reset_trim = ctk.CTkButton(
            trim_box, text="🔄 Reset về toàn bộ video", height=28,
            fg_color="#334155", hover_color="#475569", font=("Segoe UI", 11),
            command=self.callbacks.get("on_reset_trim")
        )
        self.btn_reset_trim.pack(fill="x", padx=10, pady=(0, 6))

        # Info Box đoạn cắt
        self.trim_info_box = ctk.CTkFrame(trim_box, fg_color="#0F172A", corner_radius=8)
        self.trim_info_box.pack(fill="x", padx=10, pady=(0, 6))

        self.lbl_trim_range = ctk.CTkLabel(
            self.trim_info_box, text="Đoạn cắt: [0 -> 0]", font=("Segoe UI", 12, "bold"), text_color="#38BDF8"
        )
        self.lbl_trim_range.pack(anchor="w", padx=10, pady=(6, 1))

        self.lbl_trim_duration = ctk.CTkLabel(
            self.trim_info_box, text="Thời lượng: 0 frames (0.00s)", font=("Segoe UI", 11), text_color="gray75"
        )
        self.lbl_trim_duration.pack(anchor="w", padx=10, pady=(0, 6))

        self.btn_export_video = ctk.CTkButton(
            trim_box, text="🎬 Xuất Đoạn Video Sạch (.mp4)", height=32,
            fg_color="#059669", hover_color="#047857", font=("Segoe UI", 11, "bold"),
            command=self.callbacks.get("on_export_video")
        )
        self.btn_export_video.pack(fill="x", padx=10, pady=(0, 10))

        # ==================== MỤC 3: LƯU MẪU CƠ SỞ DỮ LIỆU ====================
        self._build_header("💾 LƯU MẪU VÀO CSDL", "#A78BFA")

        save_box = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        save_box.pack(fill="x", padx=6, pady=(0, 10))

        lbl_name_hint = ctk.CTkLabel(save_box, text="Tên cử chỉ:", font=("Segoe UI", 11, "bold"), text_color="gray75")
        lbl_name_hint.pack(anchor="w", padx=10, pady=(10, 2))

        self.entry_gesture_name = ctk.CTkEntry(
            save_box, height=36, font=("Segoe UI", 13, "bold"),
            placeholder_text="vd: a, b, xin_chao, cam_on..."
        )
        self.entry_gesture_name.pack(fill="x", padx=10, pady=(0, 8))

        # Phân loại Cử chỉ Tĩnh / Động (Static / Dynamic Selector)
        self.seg_gesture_type = ctk.CTkSegmentedButton(
            save_box,
            values=["🖐️ Tĩnh (Static)", "💫 Động (Dynamic)"],
            font=("Segoe UI", 11, "bold"),
            selected_color="#2563EB",
            selected_hover_color="#1D4ED8",
            command=self._on_gesture_type_changed
        )
        self.seg_gesture_type.set("🖐️ Tĩnh (Static)")
        self.seg_gesture_type.pack(fill="x", padx=10, pady=(0, 8))

        # Checkboxes thành phần lưu
        self.save_comp_frame = ctk.CTkFrame(save_box, fg_color="#0F172A", corner_radius=8)
        self.save_comp_frame.pack(fill="x", padx=10, pady=(0, 8))

        self.lbl_comp_title = ctk.CTkLabel(
            self.save_comp_frame, text="🧩 Thành phần lưu:",
            font=("Segoe UI", 11, "bold"), text_color="#38BDF8"
        )
        self.lbl_comp_title.pack(anchor="w", padx=10, pady=(6, 2))

        self.chk_save_hand = ctk.CTkCheckBox(
            self.save_comp_frame, text="🖐️ Bàn tay (Hands - Bắt buộc)",
            font=("Segoe UI", 11, "bold"), text_color="#34D399", state="disabled"
        )
        self.chk_save_hand.select()
        self.chk_save_hand.pack(anchor="w", padx=10, pady=2)

        self.chk_save_arm = ctk.CTkCheckBox(
            self.save_comp_frame, text="🦾 Cánh tay & Vai (Arm / Pose)", font=("Segoe UI", 11)
        )
        self.chk_save_arm.pack(anchor="w", padx=10, pady=2)

        self.chk_save_head = ctk.CTkCheckBox(
            self.save_comp_frame, text="👤 Đầu & Khuôn mặt (Head / Face)", font=("Segoe UI", 11)
        )
        self.chk_save_head.pack(anchor="w", padx=10, pady=2)

        self.chk_save_video = ctk.CTkCheckBox(
            self.save_comp_frame, text="🎬 Lưu kèm Video sạch (.mp4)",
            font=("Segoe UI", 11, "bold"), text_color="#38BDF8"
        )
        self.chk_save_video.select()
        self.chk_save_video.pack(anchor="w", padx=10, pady=2)

        self.lbl_save_hint = ctk.CTkLabel(
            self.save_comp_frame,
            text="💡 Gợi ý: Cử chỉ chữ cái tĩnh chỉ cần Bàn tay.\nCử chỉ động nên chọn thêm Cánh tay.",
            font=("Segoe UI", 10), text_color="gray70", justify="left"
        )
        self.lbl_save_hint.pack(anchor="w", padx=10, pady=(2, 6))

        # Primary Master Save Button
        self.btn_save = ctk.CTkButton(
            save_box, text="💾 LƯU CỬ CHỈ (.mp4, .npy, .json)", height=44,
            fg_color="#2563EB", hover_color="#1D4ED8", font=("Segoe UI", 12, "bold"),
            command=self.callbacks.get("on_save_gesture")
        )
        self.btn_save.pack(fill="x", padx=10, pady=(2, 12))

    def _on_gesture_type_changed(self, value):
        if "Động" in value:
            self.chk_save_arm.select()
            self.lbl_save_hint.configure(
                text="💡 Cử chỉ ĐỘNG: Đã bật lưu Cánh tay để ghi nhận quỹ đạo & nhịp lắc (vd: Số 10).",
                text_color="#FBBF24"
            )
        else:
            self.chk_save_arm.deselect()
            self.lbl_save_hint.configure(
                text="💡 Cử chỉ TĨNH: Tập trung vào hình thái 21 khớp bàn tay (Bất biến góc xoay & tỉ lệ).",
                text_color="#34D399"
            )

    def _on_rec_mode_changed(self, value):
        cb = self.callbacks.get("on_rec_mode_changed")
        if cb:
            cb(value)

    def _build_header(self, title: str, accent_color: str):
        hdr = ctk.CTkLabel(self, text=title, font=("Segoe UI", 13, "bold"), text_color=accent_color)
        hdr.pack(anchor="w", padx=10, pady=(6, 4))
