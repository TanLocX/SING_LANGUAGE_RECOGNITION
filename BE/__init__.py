"""
Backend package for Sign Language Recognition System (Chuyên biệt Cử chỉ Động)
"""
from .holistic_tracker import HolisticTracker, extract_keypoints, draw_keypoints_vector
from .onnx_tracker import OnnxTracker
from .camera_stream import CameraManager
from .tts_manager import TTSManager
from .motion_spotter import KinematicMotionSpotter, MotionState
from .dynamic_recognizer import (
    DynamicGestureRecognizer,
    fast_dtw_distance,
    resample_sequence,
    normalize_dynamic_sequence,
)
from .gesture_recognizer import (
    GestureDatasetManager,
    VideoRecognizer,
    normalize_hand_landmarks,
    normalize_feature_frame,
    normalize_sequence,
    extract_active_hand_shape,
    detect_gesture_motion,
    align_hand_landmarks,
)

__all__ = [
    "HolisticTracker",
    "OnnxTracker",
    "extract_keypoints",
    "draw_keypoints_vector",
    "CameraManager",
    "TTSManager",
    "KinematicMotionSpotter",
    "MotionState",
    "DynamicGestureRecognizer",
    "GestureDatasetManager",
    "VideoRecognizer",
    "align_hand_landmarks",
    "fast_dtw_distance",
    "resample_sequence",
    "normalize_dynamic_sequence",
    "normalize_hand_landmarks",
    "normalize_feature_frame",
    "normalize_sequence",
    "extract_active_hand_shape",
    "detect_gesture_motion",
]
