import numpy as np
import cv2
import itertools

IMG = 'Snack-machine.jpg'
L1 = cv2.imread('load1.png')
L2 = cv2.imread('load2.png')
L3 = cv2.imread('load3.png')
loadframe = itertools.cycle([L1, L2, L3])


def cursor_on_snack(cursor, snack) -> bool:
    return False


class Snack:
    def __init__(self):
        self.name: str = ""
        self.loc: list = [50, 50]
        self.dim: list = [100, 100]
        self.is_selected: bool = False
        self.is_highlighted: bool = False

    def select(self, selected):
        self.is_selected = selected

    def highlight(self):
        ...

    def is_hovered(self, cursor):
        out = cursor[0] >= self.loc[0]
        out &= cursor[0] <= self.loc[0] + self.dim[0]
        out &= cursor[1] >= self.loc[1]
        out &= cursor[1] <= self.loc[1] + self.dim[1]
        return out


class VendingMachine:
    def __init__(self):
        self.snackbin: list = []
        self.image = 0
        self.populate_snackbin()

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
        for l, d in zip(locations, dimensions):
            some_snack = Snack()
            some_snack.dim = d
            some_snack.loc = l
            self.snackbin.append(some_snack)

    def draw(self, gaze, is_nodding: bool, is_dwelling: bool):
        img = self.draw_vending_machine(IMG)
        img = self.draw_snacks(gaze, img, is_dwelling)
        return img

    def draw_vending_machine(self, img):
        return cv2.imread(img)

    def draw_snacks(self, cursor, vendo, is_dwelling):
        for snack in self.snackbin:
            if snack.is_hovered(cursor):
                startpt = (snack.loc[0], snack.loc[1])
                endpt = (startpt[0] + snack.dim[0], startpt[1] + snack.dim[1])
                vendo = cv2.rectangle(vendo, startpt, endpt, (255, 0, 0), 5)
                # draw highlight on snack
                snack.highlight()
                if is_dwelling:
                    # draw loading bar on snack
                    self.wait_select(cursor, snack)
                    load = next(loadframe)
                    vendo[snack.loc[1]:snack.loc[1]+load.shape[0], snack.loc[0]:snack.loc[0]+load.shape[1]] = load
        return vendo

    def highlight_snack(self, snack):
        ...

    def wait_select(self, gaze, snack: Snack):
        # snack.draw_loadingbar()
        ...












