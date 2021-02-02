import numpy as np
import cv2
import itertools

IMG1 = 'images/Snack-machine.jpg'
IMG2 = 'images/Snack-machine2.jpg'
L1 = cv2.imread('images/load1.png')
L2 = cv2.imread('images/load2.png')
L3 = cv2.imread('images/load3.png')
loadframe = itertools.cycle([L1, L2, L3])
vendoframe = itertools.cycle([IMG1, IMG1, IMG2, IMG2])
DWELL_THRESHOLD = 5
WAIT_LIMIT = 10


def cursor_on_snack(cursor, snack) -> bool:
    return False


class Snack:
    def __init__(self):
        self.name: str = ""
        self.loc: list = [50, 50]
        self.dim: list = [100, 100]
        self.is_selected: bool = False
        self.is_highlighted: bool = False
        self.index = 0

    def select(self, selected):
        self.is_selected = selected

    def highlight(self, vendo):
        startpt = (self.loc[0], self.loc[1])
        endpt = (startpt[0] + self.dim[0], startpt[1] + self.dim[1])
        vendo = cv2.rectangle(vendo, startpt, endpt, (255, 0, 0), 5)
        return vendo

    def is_hovered_by(self, cursor):
        out = cursor[0] >= self.loc[0]
        out &= cursor[0] <= self.loc[0] + self.dim[0]
        out &= cursor[1] >= self.loc[1]
        out &= cursor[1] <= self.loc[1] + self.dim[1]
        return out

    def retrieve_snack_image(self):
        img = cv2.imread('images/snack{}.png'.format(self.index))
        return img


class VendingMachine:
    def __init__(self):
        self.snackbin: list = []
        self.image = 0
        self.populate_snackbin()
        self.last_visited_snack: Snack = None
        self.dwell_count: int = 0
        self.waiting_on_nod: bool = False
        self.wait_count: int = 10
        self.purchase_confrmed: bool = False
        self.purchase_delay_count: int = 5

    def populate_snackbin(self):
        dimensions = [
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
        locations = [
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
        for i, (l, d) in enumerate(zip(locations, dimensions)):
            some_snack = Snack()
            some_snack.dim = d
            some_snack.loc = l
            some_snack.index = i+1
            self.snackbin.append(some_snack)

    def update_dwell_details(self, gaze, vendo, current_snack: Snack):
        # if gaze on self.dwelling_on:
        if not self.waiting_on_nod:
            if self.last_visited_snack is not current_snack:
                self.dwell_count = 0
                self.last_visited_snack = current_snack
            else:
                load = next(loadframe)
                vendo[current_snack.loc[1]:current_snack.loc[1] + load.shape[0], current_snack.loc[0]:current_snack.loc[0] + load.shape[1]] = load
                self.dwell_count += 1

        self.waiting_on_nod = True if self.dwell_count >= DWELL_THRESHOLD else False

        return vendo

    def draw(self, gaze, is_nodding: bool):

        img = self.draw_vending_machine()
        if self.waiting_on_nod:
            self.wait_count -= 1
            img = self.draw_confirm_select(img, is_nodding)
            if self.wait_count < 0:
                self.waiting_on_nod = False
                self.wait_count = 10
        else:
            img = self.draw_snacks(gaze, img)

        return img

    @staticmethod
    def draw_vending_machine():
        frame = next(vendoframe)
        return cv2.imread(frame)

    def draw_snacks(self, cursor, vendo):
        for snack in self.snackbin:
            if snack.is_hovered_by(cursor):
                # vendo = snack.highlight(vendo)
                self.update_dwell_details(cursor, vendo, snack)

        return vendo

    def draw_confirm_select(self, img, is_confirming: bool):
        current_snack = self.last_visited_snack
        offset = 20
        overlay = img.copy()
        cv2.rectangle(overlay, (offset,offset), (img.shape[1]-offset,img.shape[0]-offset), (0, 0, 0), -1)
        cv2.addWeighted(overlay, .5, img, .5, 0, img)

        # Overlay snack item
        snack_img = current_snack.retrieve_snack_image()
        center_loc = (int(img.shape[0]/2), int(img.shape[1]/2))
        startingpt = (int(img.shape[0]/2) - int(snack_img.shape[0]/2),
                      int(img.shape[1]/2) - int(snack_img.shape[1]/2)
                      )
        img[startingpt[0]: startingpt[0] + snack_img.shape[0],
        startingpt[1]: startingpt[1] + snack_img.shape[1]] = snack_img

        place_text = lambda message, x_offset: cv2.putText(img, message, (int(img.shape[1]/2) + x_offset, int(img.shape[0]/2) - 250), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

        if not is_confirming:
            place_text("Purchase item? [Nod]", -175)
        else:
            self.purchase_delay_count -= 1
            place_text("Item purchased!", -130)
            if self.purchase_delay_count < 0:
                self.waiting_on_nod = False
                self.wait_count = 10
                self.purchase_delay_count = 10
            
        return img















