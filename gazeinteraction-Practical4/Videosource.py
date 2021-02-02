import threading
import cv2


class Videosource(threading.Thread):
    def __init__(self, cameraID, frameReceiver):
        super().__init__()
        self.cap = cv2.VideoCapture(cameraID)
        self.frameReceiver = frameReceiver
        self.should_run = False

    def __del__(self):
        self.should_run = False
        self.cap.release()

    def run(self):
        self.should_run = True
        while self.should_run:
            ret, frame = self.cap.read()
            if ret:
                self.frameReceiver.push_frame(frame)