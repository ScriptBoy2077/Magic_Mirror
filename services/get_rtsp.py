import cv2, threading, time

from services.config import CAMERA_RTSP, CAMERA_INTERVAL

class CameraGrabber:
    """后台线程：不断读 RTSP，把最新帧保存在内存"""
    def __init__(self):
        self.frame = None
        self.lock = threading.Lock()
        self.t = threading.Thread(target=self._grab, daemon=True)
        self.t.start()

    def _grab(self):
        cap = cv2.VideoCapture(CAMERA_RTSP)
        while True:
            ret, frame = cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:                       # 断线重连
                cap.release()
                time.sleep(2)
                cap = cv2.VideoCapture(CAMERA_RTSP)
            time.sleep(CAMERA_INTERVAL)

    def get_frame_bytes(self, quality=85):
        """返回 JPEG 二进制，可直接给 FastAPI 的 Response"""
        with self.lock:
            if self.frame is None:
                return None
            _, enc = cv2.imencode('.jpg', self.frame,
                                 [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            return enc.tobytes()


if __name__ == "__main__":
    camera = CameraGrabber()