import threading
import sys

class TTSManager:
    """
    Manages text-to-speech requests in a non-blocking background thread.
    Can use pyttsx3 if available, or print/log as fallback.
    """
    def __init__(self):
        self.enabled = True
        self.is_speaking = False
        self._engine = None
        self._init_engine()

    def _init_engine(self):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', 150)
        except Exception:
            self._engine = None

    def speak(self, text: str):
        if not self.enabled or not text.strip():
            return
            
        def _run_speak():
            self.is_speaking = True
            try:
                if self._engine:
                    self._engine.say(text)
                    self._engine.runAndWait()
                else:
                    print(f"[TTS Audio]: {text}")
            except Exception as e:
                print(f"[TTS Error]: {e}")
            finally:
                self.is_speaking = False

        t = threading.Thread(target=_run_speak, daemon=True)
        t.start()

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled
