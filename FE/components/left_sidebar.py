import customtkinter as ctk

class LeftSidebarFrame(ctk.CTkScrollableFrame):
    """
    Cột Trái - Bảng Điều Khiển Trung Tâm (Left Sidebar Dashboard):
    - Cụm 1: Các chế độ hoạt động (Live, Quay Webcam, Quét Video, Mở Biên tập)
    - Cụm 2: Thư viện & Quản lý CSDL Cử chỉ (.npy/.json)
    - Cụm 3: Cấu hình hiển thị khung xương & Thuộc tính giải phẫu
    """
    def __init__(self, master, callbacks=None, **kwargs):
        super().__init__(
            master, width=310, corner_radius=12,
            fg_color="#0F172A", border_width=1, border_color="#1E293B",
            **kwargs
        )
        self.callbacks = callbacks or {}
        self._build_ui()

    def _build_ui(self):
        # ==================== CỤM 1: CHẾ ĐỘ LÀM VIỆC ====================
        self._build_section_header("🚀 CHẾ ĐỘ HOẠT ĐỘNG", "#38BDF8")

        mode_box = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        mode_box.pack(fill="x", padx=6, pady=(0, 10))

        self.btn_live_rec = ctk.CTkButton(
            mode_box, text="🎥 Nhận Diện Trực Tiếp", height=38,
            fg_color="#7C3AED", hover_color="#6D28D9", font=("Segoe UI", 12, "bold"),
            command=self.callbacks.get("on_toggle_live")
        )
        self.btn_live_rec.pack(fill="x", padx=10, pady=(10, 4))

        self.btn_open_webcam = ctk.CTkButton(
            mode_box, text="📷 Quay Mẫu Webcam", height=38,
            fg_color="#DB2777", hover_color="#BE185D", font=("Segoe UI", 12, "bold"),
            command=self.callbacks.get("on_toggle_webcam")
        )
        self.btn_open_webcam.pack(fill="x", padx=10, pady=4)

        self.btn_rec_video = ctk.CTkButton(
            mode_box, text="🔍 Quét File Video (.npy)", height=38,
            fg_color="#059669", hover_color="#047857", font=("Segoe UI", 12, "bold"),
            command=self.callbacks.get("on_rec_video")
        )
        self.btn_rec_video.pack(fill="x", padx=10, pady=4)

        self.btn_open_video = ctk.CTkButton(
            mode_box, text="📂 Mở Video Biên Tập", height=38,
            fg_color="#0284C7", hover_color="#0369A1", font=("Segoe UI", 12, "bold"),
            command=self.callbacks.get("on_open_video")
        )
        self.btn_open_video.pack(fill="x", padx=10, pady=(4, 10))

        # ==================== CỤM 2: THƯ VIỆN & CƠ SỞ DỮ LIỆU ====================
        self._build_section_header("📁 CƠ SỞ DỮ LIỆU CỬ CHỈ", "#34D399")

        db_box = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        db_box.pack(fill="x", padx=6, pady=(0, 10))

        lbl_src = ctk.CTkLabel(db_box, text="Nguồn dữ liệu:", font=("Segoe UI", 11, "bold"), text_color="gray75")
        lbl_src.pack(anchor="w", padx=10, pady=(8, 2))

        self.seg_data_source = ctk.CTkSegmentedButton(
            db_box, values=["DATA", "Recordings", "Cả hai"],
            command=self.callbacks.get("on_data_source_change"),
            font=("Segoe UI", 11, "bold"), height=30, selected_color="#0284C7"
        )
        self.seg_data_source.set("DATA")
        self.seg_data_source.pack(fill="x", padx=10, pady=(0, 6))

        self.lbl_gesture_stats = ctk.CTkLabel(
            db_box, text="Thông tin: Đang nạp CSDL...", font=("Segoe UI", 11), text_color="#38BDF8"
        )
        self.lbl_gesture_stats.pack(anchor="w", padx=10, pady=2)

        lbl_choose = ctk.CTkLabel(db_box, text="Chọn cử chỉ xem / tinh chỉnh:", font=("Segoe UI", 11, "bold"), text_color="gray75")
        lbl_choose.pack(anchor="w", padx=10, pady=(4, 2))

        self.opt_gestures = ctk.CTkOptionMenu(
            db_box, values=["(Đang tải...)"], font=("Segoe UI", 12), height=32,
            fg_color="#334155", button_color="#475569", button_hover_color="#64748B",
            command=self.callbacks.get("on_select_manage_gesture")
        )
        self.opt_gestures.pack(fill="x", padx=10, pady=(0, 6))

        # Box tinh chỉnh thông số
        tune_box = ctk.CTkFrame(db_box, fg_color="#0F172A", corner_radius=8)
        tune_box.pack(fill="x", padx=10, pady=(2, 8))

        lbl_th_row = ctk.CTkFrame(tune_box, fg_color="transparent")
        lbl_th_row.pack(fill="x", padx=8, pady=(4, 0))
        ctk.CTkLabel(lbl_th_row, text="Ngưỡng sai số:", font=("Segoe UI", 10), text_color="gray70").pack(side="left")
        self.lbl_mg_thresh_val = ctk.CTkLabel(lbl_th_row, text="0.45", font=("Segoe UI", 10, "bold"), text_color="#38BDF8")
        self.lbl_mg_thresh_val.pack(side="right")

        self.slider_mg_thresh = ctk.CTkSlider(
            tune_box, from_=0.15, to=0.85, height=14,
            command=self.callbacks.get("on_mg_thresh_change")
        )
        self.slider_mg_thresh.set(0.45)
        self.slider_mg_thresh.pack(fill="x", padx=8, pady=(2, 6))

        lbl_fr_row = ctk.CTkFrame(tune_box, fg_color="transparent")
        lbl_fr_row.pack(fill="x", padx=8, pady=(2, 0))
        ctk.CTkLabel(lbl_fr_row, text="Số frame yêu cầu:", font=("Segoe UI", 10), text_color="gray70").pack(side="left")
        self.lbl_mg_frames_val = ctk.CTkLabel(lbl_fr_row, text="Mặc định", font=("Segoe UI", 10, "bold"), text_color="#38BDF8")
        self.lbl_mg_frames_val.pack(side="right")

        self.slider_mg_frames = ctk.CTkSlider(
            tune_box, from_=0, to=60, number_of_steps=60, height=14,
            command=self.callbacks.get("on_mg_frames_change")
        )
        self.slider_mg_frames.set(0)
        self.slider_mg_frames.pack(fill="x", padx=8, pady=(2, 8))

        self.entry_mg_display_text = ctk.CTkEntry(
            tune_box, placeholder_text="Tên hiển thị khi nhận diện...", font=("Segoe UI", 11), height=28
        )
        self.entry_mg_display_text.pack(fill="x", padx=8, pady=(0, 6))

        db_btn_row = ctk.CTkFrame(db_box, fg_color="transparent")
        db_btn_row.pack(fill="x", padx=10, pady=(0, 10))

        self.btn_save_mg = ctk.CTkButton(
            db_btn_row, text="💾 Lưu Chỉnh", width=130, height=30,
            fg_color="#0284C7", hover_color="#0369A1", font=("Segoe UI", 11, "bold"),
            command=self.callbacks.get("on_save_mg")
        )
        self.btn_save_mg.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_del_mg = ctk.CTkButton(
            db_btn_row, text="🗑️ Xóa Mẫu", width=100, height=30,
            fg_color="#DC2626", hover_color="#B91C1C", font=("Segoe UI", 11, "bold"),
            command=self.callbacks.get("on_delete_mg")
        )
        self.btn_del_mg.pack(side="right", expand=True, fill="x", padx=(4, 0))

        # ==================== CỤM 3: CẤU HÌNH HIỂN THỊ & THUỘC TÍNH ====================
        self._build_section_header("⚙️ CẤU HÌNH & HIỂN THỊ", "#F59E0B")

        opt_box = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        opt_box.pack(fill="x", padx=6, pady=(0, 10))

        lbl_h_mode = ctk.CTkLabel(opt_box, text="Số lượng tay theo dõi:", font=("Segoe UI", 11, "bold"), text_color="gray75")
        lbl_h_mode.pack(anchor="w", padx=10, pady=(8, 2))

        self.seg_hands = ctk.CTkSegmentedButton(
            opt_box, values=["1 Tay", "2 Tay"], font=("Segoe UI", 11, "bold"),
            command=self.callbacks.get("on_hand_mode_change"), height=28, selected_color="#0284C7"
        )
        self.seg_hands.set("2 Tay")
        self.seg_hands.pack(fill="x", padx=10, pady=(0, 4))

        lbl_override = ctk.CTkLabel(opt_box, text="Ép nhãn bên tay (khi dùng 1 tay):", font=("Segoe UI", 11), text_color="gray70")
        lbl_override.pack(anchor="w", padx=10, pady=(2, 2))

        self.seg_hand_side = ctk.CTkSegmentedButton(
            opt_box, values=["Tự động", "Phải", "Trái"], font=("Segoe UI", 11),
            command=self.callbacks.get("on_hand_side_override_change"), height=26
        )
        self.seg_hand_side.set("Tự động")
        self.seg_hand_side.pack(fill="x", padx=10, pady=(0, 6))

        self.btn_swap_hands = ctk.CTkButton(
            opt_box, text="🔄 Đổi Nhãn Trái ↔ Phải", height=28,
            fg_color="#475569", hover_color="#334155", font=("Segoe UI", 11),
            command=self.callbacks.get("on_swap_hands")
        )
        self.btn_swap_hands.pack(fill="x", padx=10, pady=(0, 8))

        # Checkboxes hiển thị khung xương
        chk_container = ctk.CTkFrame(opt_box, fg_color="#0F172A", corner_radius=8)
        chk_container.pack(fill="x", padx=10, pady=(0, 8))

        self.chk_landmarks = ctk.CTkCheckBox(chk_container, text="Khung xương bàn tay", font=("Segoe UI", 11))
        self.chk_landmarks.select()
        self.chk_landmarks.pack(anchor="w", padx=8, pady=3)

        self.chk_arm_pose = ctk.CTkCheckBox(chk_container, text="Khung cánh tay & vai (Pose)", font=("Segoe UI", 11))
        self.chk_arm_pose.select()
        self.chk_arm_pose.pack(anchor="w", padx=8, pady=3)

        self.chk_head_tracker = ctk.CTkCheckBox(chk_container, text="Khuôn mặt & đầu (Face)", font=("Segoe UI", 11))
        self.chk_head_tracker.select()
        self.chk_head_tracker.pack(anchor="w", padx=8, pady=3)

        self.chk_trail = ctk.CTkCheckBox(chk_container, text="Vẽ vệt quỹ đạo cử chỉ", font=("Segoe UI", 11))
        self.chk_trail.select()
        self.chk_trail.pack(anchor="w", padx=8, pady=3)

        self.chk_rec_hud = ctk.CTkCheckBox(chk_container, text="Hiện nhãn nhận diện trên video", font=("Segoe UI", 11))
        self.chk_rec_hud.select()
        self.chk_rec_hud.pack(anchor="w", padx=8, pady=3)

        self.chk_geom_norm = ctk.CTkCheckBox(chk_container, text="Chuẩn hóa hình học đồng dạng", font=("Segoe UI", 11))
        self.chk_geom_norm.select()
        self.chk_geom_norm.pack(anchor="w", padx=8, pady=3)

        self.chk_interp = ctk.CTkCheckBox(chk_container, text="Chống mất tay khi che khuất", font=("Segoe UI", 11))
        self.chk_interp.select()
        self.chk_interp.pack(anchor="w", padx=8, pady=(3, 6))

        # Slider độ trễ xác nhận
        stable_row = ctk.CTkFrame(opt_box, fg_color="transparent")
        stable_row.pack(fill="x", padx=10, pady=(2, 0))
        ctk.CTkLabel(stable_row, text="Độ trễ xác nhận:", font=("Segoe UI", 11, "bold"), text_color="gray75").pack(side="left")
        self.lbl_stable_val = ctk.CTkLabel(stable_row, text="6 frames (~200ms)", font=("Segoe UI", 11), text_color="#38BDF8")
        self.lbl_stable_val.pack(side="right")

        self.slider_stable = ctk.CTkSlider(
            opt_box, from_=1, to=15, number_of_steps=14, height=14,
            command=self.callbacks.get("on_stable_slider_change")
        )
        self.slider_stable.set(6)
        self.slider_stable.pack(fill="x", padx=10, pady=(2, 10))

    def _build_section_header(self, title: str, accent_color: str):
        hdr = ctk.CTkLabel(self, text=title, font=("Segoe UI", 13, "bold"), text_color=accent_color)
        hdr.pack(anchor="w", padx=10, pady=(8, 4))
