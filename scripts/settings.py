# Modules
import pygame
import pickle
from pygame.constants import *
import logging

# Scripts
from scripts.input import Controls

logger = logging.getLogger(__name__)

class Settings:
    def __init__(self):
        self.resolution = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self.targetFPS = 120
        self.keyboard = Controls(K_d, K_a, K_s, K_w, K_LSHIFT, K_ESCAPE, K_SPACE, K_r)
        self.controller = Controls(0, 0, 1, 1, 1, 7, 100, 2)

    @property
    def width(self):
        return self.resolution[0]
    
    @property
    def height(self):
        return self.resolution[1]

    def save_to_file(self, filename):
        try:
            with open(filename, 'wb') as file:
                pickle.dump(self, file)
            print("Settings saved successfully.")
        except Exception as e:
            print(f"Error while saving settings: {e}")

    @staticmethod
    def load_from_file(filename):
        try:
            with open(filename, 'rb') as file:
                settings = pickle.load(file)
            print("Settings loaded successfully.")
            return settings
        except Exception as e:
            print(f"Error while loading settings: {e}")
            return Settings()