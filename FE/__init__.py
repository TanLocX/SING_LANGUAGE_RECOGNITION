"""
Frontend UI package for Sign Language Recognition System
=========================================================
Bố cục 3 Cột (Professional Dashboard):
  - TopBarFrame: Header & Thanh tiến trình
  - LeftSidebarFrame: Cột trái (Chế độ & CSDL cử chỉ & Cấu hình)
  - VideoCanvasFrame: Cột giữa (Canvas + Timeline + TTS)
  - RightPanelFrame: Cột phải (Kết quả nhận diện + Cắt frame + Lưu mẫu)
"""
from .top_bar import TopBarFrame
from .left_sidebar import LeftSidebarFrame
from .video_canvas import VideoCanvasFrame
from .right_panel import RightPanelFrame

__all__ = ["TopBarFrame", "LeftSidebarFrame", "VideoCanvasFrame", "RightPanelFrame"]
