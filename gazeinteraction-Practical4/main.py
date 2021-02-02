from Eyetracker import Eyetracker, GazeObserver
from Calibration import Calibration
import cv2
import numpy as np
from SmoothingFilter import RingBuffer
from Button import Button
from VendingMachine import VendingMachine


IMG = 'Snack-machine.jpg'
RADIUS = 10
COLOR = (0, 255, 0)


class Mainloop(GazeObserver):
    def __init__(self):
        self.button = Button()
        self.eye = Eyetracker(1)
        self.eye.subscribe(self)
        self.eye.start()
        self.vendo = VendingMachine()

        self.on_mouse_mode = True
        self.mouse_coord = [0, 0]

        # trigger
        self.is_nodding: bool = False
        self.is_staring: bool = False

        # CALIBRATION
        self.calibration = Calibration()
        self.imsize = (898, 1500)
        border = 10
        x_step = (self.imsize[1]-border*2)/2
        y_step = (self.imsize[0]-border*2)/2
        self.stim_pos = []
        for x in range(3):
            for y in range(3):
                self.stim_pos.append([int(border+x_step*x), int(border+y_step*y)])
        # self.stim_pos.extend(self.stim_pos)
        self.current_stim = 0
        # CALIBRATION

        # FILTER
        self.smoother = RingBuffer(1)
        # FILTER

    def __del__(self):
        self.eye.join()

    def update_gaze(self, gaze, frame):
        cv2.imshow('Eyetracker', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        click_cal = lambda event, x, y, flags, param: self.click_calibrate(event, x, y, gaze)

        # CALIBRATION
        calibration_img = np.zeros((self.imsize[0], self.imsize[1], 3))
        if self.calibration.is_calibrating:
            radius = 5
            cv2.circle(calibration_img, (self.stim_pos[self.current_stim][0], self.stim_pos[self.current_stim][1]), radius,
                       (255, 255, 255), -1)
            self.calibration.push_sample((gaze[0], gaze[1]), self.stim_pos[self.current_stim])
        else:
            # calibration_img = cv2.imread(IMG)
            gaze = self.mouse_coord if self.on_mouse_mode else self.calibration.apply_calibration((gaze[0], gaze[1]))
            self.smoother.append(gaze)

            gaze = self.smoother.get_mean()
            # draw the vending machine gui
            calibration_img = self.vendo.draw(gaze, self.is_nodding, self.is_staring)
            # draw current gaze loc
            cv2.circle(calibration_img, (int(gaze[0]), int(gaze[1])), RADIUS, COLOR, -1)
        cv2.imshow("stimulus", calibration_img)

        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            self.eye.should_run = False
        if key & 0xFF == ord('a'):
            self.current_stim = self.current_stim + 1
            if self.current_stim == len(self.stim_pos):
                self.calibration.calibrate()
        # for debugging purposes
        if key & 0xFF == ord('n'):
            self.is_nodding = not self.is_nodding
            print("is_nodding", self.is_nodding)
        if key & 0xFF == ord('h'):
            self.is_staring = not self.is_staring
            print("is_staring", self.is_staring)

        if not self.calibration.is_calibrating:
            cv2.setMouseCallback("stimulus", click_cal)

    # do if event
    def click_calibrate(self, event, x, y, gaze):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.calibration.push_sample((gaze[0], gaze[1]), [x, y])
            self.calibration.calibrate()
            print("New calibration point at", x, y)
            with open('aoi_locs.txt', 'a') as file:
                file.write(' '.join([str(x), str(y)])+'\n')

        self.mouse_coord = [x, y]


    def update_nod(self, is_nodding: bool):
        if self.is_nodding is not is_nodding:
            self.is_nodding = is_nodding
            update_text = "NOT " if not is_nodding else ""
            print("YOU'RE {}NODDING!".format(update_text))

    def update_stare(self, is_staring: bool):
        if self.is_staring is not is_staring:
            self.is_staring = is_staring
            update_text = "NOT " if not is_staring else ""
            print("YOU'RE {}NODDING!".format(update_text))


main = Mainloop()

