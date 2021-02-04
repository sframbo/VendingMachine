import os
import sys
import cv2
import time
import torch
import utils
import argparse
import traceback
import numpy as np
from PIL import Image
from models import gazenet
from mtcnn import FaceDetector
import threading
from Videosource import Videosource
from abc import ABC
from typing import Sequence
import queue

from NodDetector import NodDetector


class GazeObserver(ABC):
    def update_gaze(self, gaze, frame):
        pass


class Eyetracker(threading.Thread):
    def __init__(self, cameraID, nod_detector):
        super().__init__()
        print('Loading MobileFaceGaze model...')
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = gazenet.GazeNet(device)

        if not torch.cuda.is_available():
            print('Running on CPU.')
        else:
            print('Running on GPU.')

        state_dict = torch.load('models/weights/gazenet.pth', map_location=device)
        self.model.load_state_dict(state_dict)
        print('Model loaded using {} as device'.format(device))

        self.model.eval()

        self.face_detector = FaceDetector(device=device)

        self.queue_capacity = 10
        self.frame_buffer = queue.Queue()
        self.subscribers = []
        self.should_run = False

        # Setup the camera
        self.video = Videosource(cameraID, self)
        self.video.start()

        # Nod detector
        self.nod_detector: NodDetector = nod_detector

    def __del__(self):
        cv2.destroyAllWindows()
        self.video.join()

    def subscribe(self, subscriber: GazeObserver):
        assert (isinstance(subscriber, GazeObserver))
        self.subscribers.append(subscriber)

    def unsubscribe(self, subscriber):
        assert (isinstance(subscriber, GazeObserver))
        self.subscribers.remove(subscriber)

    def notify(self, gaze: Sequence[float], frame: np.ndarray):
        for subscriber in self.subscribers:
            subscriber.update_gaze(gaze, frame)

    def push_frame(self, frame: np.ndarray):
        self.frame_buffer.put(frame)

    def run(self):
        self.should_run = True
        while self.should_run:
            self.__drop_queue_if_necessary()

            # Process the next frame
            if not self.frame_buffer.empty():
                self.__process_frame()
        self.video.should_run = False

    def __drop_queue_if_necessary(self):
        # Drop frames that exceed the capacity
        already_dropped: bool = False
        while self.frame_buffer.qsize() > self.queue_capacity:  # enforce a maximal size = delay
            # if not already_dropped:
            # print("Dropping frame due to processing load!")
            self.frame_buffer.get()
            already_dropped = True

    def __process_frame(self):
        assert (not self.frame_buffer.empty())
        frame = self.frame_buffer.get()
        frame = frame[:, :, ::-1]
        frame = cv2.flip(frame, 1)
        img_h, img_w, _ = np.shape(frame)
        # Detect Faces
        display = frame.copy()
        faces, landmarks = self.face_detector.detect(Image.fromarray(frame))

        if len(faces) != 0:

            ###################################### NOD DETECTOR START
            is_nodding = self.nod_detector.detect_nodding(frame)
            for subscriber in self.subscribers:
                subscriber.update_nod(is_nodding)
            ###################################### NOD DETECTOR END

            for f, lm in zip(faces, landmarks):
                # Confidence check
                if f[-1] > 0.98:
                    # Crop and normalize face
                    face, gaze_origin, M = utils.normalize_face(lm, frame)
                    # Predict gaze
                    with torch.no_grad():
                        gaze = self.model.get_gaze(face)
                        gaze = gaze[0].data.cpu()
                        gaze = gaze.numpy()
                        gaze_new = [0,0]
                        gaze_new[0] = -200 * np.sin(gaze[1])
                        gaze_new[1] = -200 * np.sin(gaze[0])
                        # Draw results
                    display = cv2.circle(display, gaze_origin, 3, (0, 255, 0), -1)
                    display = utils.draw_gaze(display, gaze_origin, gaze, color=(255, 0, 0), thickness=2)
                    self.notify(gaze_new, display)
        else:
            print('no face detected')
