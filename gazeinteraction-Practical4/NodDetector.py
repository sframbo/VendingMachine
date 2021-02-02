import cv2
import os
import urllib.request as urlreq
import numpy as np

NOD_THRESHOLD = 20


class NodDetector():
    """
    Requirement: Video must only have one face.
    Receive a face
    Detect landmarks of face
    Lowest boundary landmark is saved (this should mark the chin)
    Next iteration -> Check if lowest boundary has considerable change in y position (face is nodding)
    If nod detected, return true
    """
    def __init__(self):
        self.previous_y: int = None
        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.landmark_detector = None

        self.get_detector()

    def get_detector(self):
        LBFmodel_url = "https://github.com/kurnianggoro/GSOC2017/raw/master/data/lbfmodel.yaml"
        LBFmodel = "lbfmodel.yaml"
        if LBFmodel in os.listdir(os.curdir):
            print("File exists")
        else:
            # download picture from url and save locally as lbfmodel.yaml, < 54MB
            urlreq.urlretrieve(LBFmodel_url, LBFmodel)
            print("File downloaded")

        self.landmark_detector = cv2.face.createFacemarkLBF()
        self.landmark_detector.loadModel(LBFmodel)

    def detect_landmarks(self, image):
        # returns the landmarks and index of largest face
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(image_gray)

        _, landmarks = self.landmark_detector.fit(image_gray, faces)
        biggest = np.argmax(faces[:, 2])

        return landmarks, biggest

    def detect_nodding(self, image):
        current_landmarks, chosen_ind = self.detect_landmarks(image)
        current_landmarks = current_landmarks[chosen_ind]

        current_y = self.get_chin(current_landmarks)

        if self.previous_y is None:
            self.previous_y = current_y
            return False
        elif abs(current_y - self.previous_y) > NOD_THRESHOLD:
            self.previous_y = current_y
            return True
        else:
            self.previous_y = current_y
            return False

    def get_average_y(self, landmarks) -> int:
        chins = [self.get_chin(l) for l in landmarks]
        return np.average(chins)

    def get_chin(self, landmark) -> int:
        ys = landmark[0, :, 1]
        ind = np.argmin(ys)
        return int(ys[ind])