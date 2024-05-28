import pygame
from pygame.constants import *

from scripts.entities import Entity

class PowerUp(Entity):
    def __init__(self, transform:tuple[int, int], size:tuple[int, int], tag:str, assets, camLayer=0, isScroll=True, animation="idle"):
        super().__init__(transform, size, tag, assets, camLayer, isScroll, animation)
        self.maxDuration = 20
        self.currentDuration = 20
        self.isPickedUp = False

    def update_timers(self, dt):
        if self.isPickedUp:
            if self.currentDuration < 0:
                self.kill()
            elif self.currentDuration > 0:
                self.currentDuration -= dt
            self.hide = True
    