import numpy as np
import cv2
import itertools
from playsound import playsound


PURCHASESFX = 'music/purchase.wav'
HOVERSFX = 'music/hover.wav'
IMG1 = 'images/Snack-machine.jpg'
IMG2 = 'images/Snack-machine2.jpg'
L1 = cv2.imread('images/load1.png')
L2 = cv2.imread('images/load2.png')
L3 = cv2.imread('images/load3.png')
loadframe = itertools.cycle([L1, L2, L3])
vendoframe = itertools.cycle([IMG1, IMG1, IMG2, IMG2])
DWELL_THRESHOLD = 5
WAIT_LIMIT = 10
DIMENSIONS = [
              [233, 211]
            , [178, 237]
            , [107, 233]
            , [221, 222]
            , [108, 232]
            , [120, 226]
            , [233, 245]
            , [204, 231]
            , [150, 234]
            , [197, 238]
            , [115, 238]
            , [134, 217]
        ]
LOCATIONS = [
              [75, 80]
            , [331, 74]
            , [533, 80]
            , [658, 73]
            , [880, 73]
            , [999, 71]
            , [75, 315]
            , [313, 330]
            , [514, 330]
            , [663, 317]
            , [870, 321]
            , [992, 321]
    ]


class Snack:
    def __init__(self, loc, dim, index):
        self.name: str = ""
        self.loc: list = loc
        self.dim: list = dim
        self.is_selected: bool = False
        self.is_highlighted: bool = False
        self.index = index + 1
        self.snack_image = cv2.imread('images/snack{}.png'.format(self.index))

    def select(self, selected):
        self.is_selected = selected

    def highlight(self, vendo):
        startpt = (self.loc[0], self.loc[1])
        endpt = (startpt[0] + self.dim[0], startpt[1] + self.dim[1])
        vendo = cv2.rectangle(vendo, startpt, endpt, (255, 0, 0), 5)
        return vendo

    def is_hovered(self, cursor) -> bool:
        out = cursor[0] >= self.loc[0]
        out &= cursor[0] <= self.loc[0] + self.dim[0]
        out &= cursor[1] >= self.loc[1]
        out &= cursor[1] <= self.loc[1] + self.dim[1]
        return out

    def get_snack_image(self):
        return self.snack_image


class VendingMachine:
    def __init__(self):
        self.snackbin: list = []
        self.image = 0

        self.last_visited_snack: Snack = None
        self.dwell_count: int = 5

        self.waiting_on_nod: bool = False
        self.nod_wait_count: int = 10

        self.purchase_confirmed: bool = False
        self.purchase_delay_count: int = 5

        self.is_cursor_active: bool = True

        self.orbiter: Orbit = Orbit()
        self.is_orbiting: bool = False

        self.is_paying: bool = False

        self.populate_snackbin()

    def populate_snackbin(self):
        self.snackbin = [Snack(dim=d, loc=l, index=i) for i, (l, d) in enumerate(zip(LOCATIONS, DIMENSIONS))]

    def draw(self, gaze, is_nodding: bool):
        img = self.draw_vending_machine()

        if self.waiting_on_nod:
            self.draw_confirm_select(img, is_nodding)
        elif self.purchase_confirmed and self.purchase_delay_count > 0:
            self.draw_purchase()
        elif self.is_orbiting:
            # when purchase confirmed, self.is_orbiting is toggled true
            target_pos = self.draw_orbit()
            self.update_orbit_details(target_pos, gaze)
        elif self.is_paying:
            # draw a text like "PAYMENT SUCCESSFUL!"
            ...
        else:
            self.draw_if_hovered(gaze, img)

        return img

    def update_orbit_details(self, target_pos, gaze):
        orbit = self.orbiter.track_orbit(gaze, target_pos)
        if orbit is not None:
            self.is_orbiting = False
            self.is_paying = orbit

    def update_dwell_details(self, gaze, vendo, current_snack: Snack):
        if not self.waiting_on_nod:
            if self.last_visited_snack is not current_snack:  # entering new aoi
                self.dwell_count = 5
                self.last_visited_snack = current_snack
            else:
                load = next(loadframe)
                vendo[current_snack.loc[1]:current_snack.loc[1] + load.shape[0], current_snack.loc[0]:current_snack.loc[0] + load.shape[1]] = load
                self.dwell_count -= 1

        self.waiting_on_nod = True if self.dwell_count <= 0 else False

        return vendo

    def update_confirm_details(self, is_confirming):
        self.nod_wait_count -= 1

        # reset if no nod action is done
        if self.nod_wait_count < 0:
            self.waiting_on_nod = False
            self.nod_wait_count = 10

        if is_confirming:
            self.purchase_delay_count -= 1
            if self.purchase_delay_count < 0:
                self.waiting_on_nod = False
                self.nod_wait_count = 10
                self.purchase_delay_count = 10

    @staticmethod
    def draw_vending_machine():
        frame = next(vendoframe)
        return cv2.imread(frame)

    def draw_if_hovered(self, cursor, vendo):
        for snack in self.snackbin:
            if snack.is_hovered(cursor):
                # vendo = snack.highlight(vendo)
                self.update_dwell_details(cursor, vendo, snack)

    def draw_confirm_select(self, img, is_confirming: bool):
        offset = 0
        overlay = img.copy()

        # draw background
        cv2.rectangle(overlay, (offset,offset), (img.shape[1]-offset,img.shape[0]-offset), (0, 0, 0), -1)
        cv2.addWeighted(overlay, .5, img, .5, 0, img)

        # Overlay snack item
        snack_img = self.last_visited_snack.get_snack_image()
        startingpt = (int(img.shape[0]/2) - int(snack_img.shape[0]/2),
                      int(img.shape[1]/2) - int(snack_img.shape[1]/2))
        img[startingpt[0]: startingpt[0] + snack_img.shape[0],
            startingpt[1]: startingpt[1] + snack_img.shape[1]] = snack_img

        place_text = lambda message, x_offset: cv2.putText(img, message, (
            int(img.shape[1] / 2) + x_offset, int(img.shape[0] / 2) - 250), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                                                           (255, 255, 255),
                                                           3)
        self.update_confirm_details(is_confirming)

        if not is_confirming:
            place_text("Purchase item? [Nod]", -175)
        else:
            self.waiting_on_nod = False
            place_text("Item purchased!", -130)
            self.activate_purchase()

    def draw_purchase(self):
        self.purchase_delay_count -= 1
        # draw something cool too i guess

    def activate_purchase(self):
        self.purchase_confirmed = True
        playsound(PURCHASESFX)

    def draw_orbit(self):
        ...
        return 0


class Orbit:
    def __init__(self):
        self.time_window: int = 5
        self.threshold: float = .8

        # both target_pos and cursor_pos must be updated at the same time
        self.target_pos: list = []
        self.gaze_pos: list = []

    def calculate_pearson(self):
        assert len(self.target_pos) != 0
        assert len(self.gaze_pos) != 0

        self.target_pos = np.array(self.target_pos)
        self.gaze_pos = np.array(self.gaze_pos)

        min_coeff = np.min([np.corrcoef(self.target_pos[:, i], self.gaze_pos[:, i]) for i in range(2)])

        return min_coeff

    def track_orbit(self, gaze, target):
        if self.time_window <= 0:
            out = self.calculate_pearson() > self.threshold
            self.reset()
            return out
        else:
            self.time_window -= 1
            self.target_pos.append(target)
            self.gaze_pos.append(gaze)
            return None

    def reset(self):
        self.time_window: int = 5
        self.target_pos: list = []
        self.gaze_pos: list = []















