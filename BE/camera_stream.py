import cv2
import time
import threading

class CameraManager:
    """
    High-Performance Threaded Camera Manager.
    Runs video capture in a dedicated background thread to eliminate I/O blocking
    and unlock full 30-60 FPS performance from the camera sensor.
    """
    def __init__(self, camera_index=0, target_width=640, target_height=480):
        self.camera_index = camera_index
        self.target_width = target_width
        self.target_height = target_height
        
        self.cap = None
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()
        
        self.latest_frame = None
        self.new_frame_event = threading.Event()
        
        # FPS Calculation
        self.prev_time = 0
        self.fps = 0.0

    def open(self, camera_index=None):
        if camera_index is not None:
            self.camera_index = camera_index

        self.release()

        # Try DirectShow first on Windows
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap or not self.cap.isOpened():
            return False

        # Attempt to set MJPG codec for maximum hardware FPS
        try:
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        except Exception:
            pass

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Read first frame to ensure camera is responsive
        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.release()
            return False

        self.latest_frame = frame
        self.is_running = True
        self.prev_time = time.time()
        self.fps = 30.0

        # Start capture background thread
        self.thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.thread.start()
        return True

    def _capture_worker(self):
        """Continuously pulls frames from the camera in background."""
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and frame is not None:
                with self.lock:
                    self.latest_frame = frame
                self.new_frame_event.set()
            else:
                time.sleep(0.01)

    def read_frame(self):
        """
        Instantly returns the latest available frame without blocking.
        Returns: (success: bool, frame: np.ndarray or None)
        """
        if not self.is_running or not self.cap or not self.cap.isOpened():
            return False, None

        with self.lock:
            frame = self.latest_frame.copy() if self.latest_frame is not None else None

        if frame is not None:
            curr_time = time.time()
            dt = curr_time - self.prev_time
            if dt > 0:
                inst_fps = 1.0 / dt
                self.fps = 0.9 * self.fps + 0.1 * inst_fps
            self.prev_time = curr_time
            return True, frame

        return False, None

    def get_fps(self):
        return round(self.fps, 1)

    def is_opened(self):
        return self.is_running and self.cap is not None and self.cap.isOpened()

    def release(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)
        self.thread = None

        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        self.latest_frame = None
