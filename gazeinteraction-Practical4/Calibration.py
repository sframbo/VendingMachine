import numpy as np
from typing import Sequence


class Calibration:
    def __init__(self):
        self.gaze_samples = []
        self.stimulus_samples = []
        self.is_calibrating = True     # A flag to indicate whether the calibration is currently running (=accepting samples)
        self.coefficients_x = None     # Holds the calibrated coefficients of the polynomial (for the x- and y-coordinate separately)
        self.coefficients_y = None

    # This function gets called during calibration and adds one gaze estimate sample and one target position on the screen to the arrays.
    def push_sample(self, gaze, stimulus):
        if self.is_calibrating:
            self.gaze_samples.append(gaze)
            self.stimulus_samples.append(stimulus)

    # Calculate the polynomial for a set of input coordinates. These are the raw gaze estimates as delivered by the eyetracker. It should return the gaze coordinate on screen.
    @staticmethod
    def polynomial_2nd_order(x, y):
        return np.array(
            [1 if np.isscalar(x) else np.ones(len(x)), x, y, x * y, x ** 2, y ** 2, x * y ** 2, x ** 2 * y]).T

    def calibrate(self):
        self.is_calibrating = False

        # Prepare data vectors
        X = np.array(self.gaze_samples)[:, 0].flatten()        # raw gaze coordinates X
        Y = np.array(self.gaze_samples)[:, 1].flatten()
        t_x = np.array(self.stimulus_samples)[:, 0].flatten()  # coordinate of the calibration marker on the screen
        t_y = np.array(self.stimulus_samples)[:, 1].flatten()

        # actual fit
        polynomial = Calibration.polynomial_2nd_order(X, Y)
        self.coefficients_x = np.linalg.lstsq(polynomial, t_x, rcond=None)[0]
        self.coefficients_y = np.linalg.lstsq(polynomial, t_y, rcond=None)[0]

    def apply_calibration(self, gaze: Sequence[float]) -> Sequence[float]:
        return np.matmul(Calibration.polynomial_2nd_order(gaze[0], gaze[1]),
                         np.array([self.coefficients_x, self.coefficients_y]).T)
