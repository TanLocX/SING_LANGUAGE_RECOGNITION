import customtkinter as ctk

class TopBarFrame(ctk.CTkFrame):
    """
    Thanh Tiêu Đề & Trạng Thái Hệ Thống (Top Header Bar):
    - Logo & Tên phần mềm chuẩn Studio chuyên nghiệp
    - Thanh thông báo trạng thái & đường dẫn tệp đang làm việc
    - Thanh tiến trình quét video tự động hiện/ẩn
    """
    def __init__(self, master, callbacks=None, **kwargs):
        super().__init__(
            master, height=52, corner_radius=12,
            fg_color="#0F172A", border_width=1, border_color="#1E293B",
            **kwargs
        )
        self.callbacks = callbacks or {}
        self._build_ui()

    def _build_ui(self):
        # 1. Main row
        self.main_row = ctk.CTkFrame(self, fg_color="transparent")
        self.main_row.pack(fill="x", padx=14, pady=8)

        # Branding
        self.lbl_brand = ctk.CTkLabel(
            self.main_row, text="🤟 SIGN LANGUAGE STUDIO",
            font=("Segoe UI", 15, "bold"), text_color="#38BDF8"
        )
        self.lbl_brand.pack(side="left", padx=(0, 8))

        self.badge_version = ctk.CTkLabel(
            self.main_row, text=" PRO v1.1 ", font=("Segoe UI", 10, "bold"),
            fg_color="#1E293B", text_color="#34D399", corner_radius=6
        )
        self.badge_version.pack(side="left", padx=(0, 14))

        # Status & File info
        self.lbl_file_path = ctk.CTkLabel(
            self.main_row, text="Sẵn sàng. Hãy chọn chế độ hoạt động ở cột bên trái để bắt đầu.",
            font=("Segoe UI", 12), text_color="gray75"
        )
        self.lbl_file_path.pack(side="left", padx=8, fill="x", expand=True)

        # Hardware engine switch (GPU RTX 3050 vs CPU)
        self.seg_engine = ctk.CTkSegmentedButton(
            self.main_row,
            values=["⚡ GPU (RTX 3050)", "💻 CPU (MediaPipe)"],
            font=("Segoe UI", 11, "bold"),
            selected_color="#7C3AED",
            selected_hover_color="#6D28D9",
            command=self.callbacks.get("on_engine_change")
        )
        self.seg_engine.set("⚡ GPU (RTX 3050)")
        self.seg_engine.pack(side="right", padx=(8, 0))

        # 2. Scanning Progress Bar (Hiện động khi quét)
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent", height=14)

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, height=6, progress_color="#10B981", fg_color="#1E293B"
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(14, 8), pady=(0, 4))

        self.lbl_progress = ctk.CTkLabel(
            self.progress_frame, text="", font=("Segoe UI", 10, "bold"), text_color="#34D399", width=180
        )
        self.lbl_progress.pack(side="right", padx=(0, 14), pady=(0, 4))

    def set_progress(self, val: float, text: str = ""):
        if val > 0:
            if not self.progress_frame.winfo_ismapped():
                self.progress_frame.pack(fill="x", padx=4, pady=(0, 4))
            self.progress_bar.set(min(1.0, max(0.0, val)))
            self.lbl_progress.configure(text=text)
        else:
            self.progress_frame.pack_forget()
            self.progress_bar.set(0)
            self.lbl_progress.configure(text="")
