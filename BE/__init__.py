"""
Backend Package for Sign Language Recognition System (BE Layer)
Organized into:
  - BE.trackers: HolisticTracker, OnnxTracker, CameraManager
  - BE.dynamic: DynamicGestureRecognizer, KinematicMotionSpotter, MotionState, FastDTW
  - BE.static: StaticGestureRecognizer
  - BE.utils: GestureDatasetManager, VideoRecognizer, TTSManager
"""

from .trackers.holistic_tracker import HolisticTracker, extract_keypoints, draw_keypoints_vector
from .trackers.onnx_tracker import OnnxTracker
from .trackers.camera_stream import CameraManager
from .utils.tts_manager import TTSManager
from .dynamic.motion_spotter import KinematicMotionSpotter, MotionState
from .dynamic.dynamic_recognizer import (
    DynamicGestureRecognizer,
    fast_dtw_distance,
    resample_sequence,
    normalize_dynamic_sequence,
)
from .static.static_recognizer import StaticGestureRecognizer
from .utils.gesture_recognizer import (
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
    "StaticGestureRecognizer",
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
