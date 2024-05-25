# Modules
import pygame
import json
import os
import logging

logger = logging.getLogger(__name__)

# Animation System
class Animation:
    def __init__(self, images, img_dur=0.2, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
        self.time_elapsed = 0
    
    # Returns a copy of itself
    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    # Updates the current frame (uses deltatime)
    def update(self, dt):
        self.time_elapsed += dt
        while self.time_elapsed >= self.img_duration:
            self.time_elapsed -= self.img_duration
            if self.loop:
                self.frame = (self.frame + 1) % len(self.images)
            else:
                self.frame = min(self.frame + 1, len(self.images) - 1)
                if self.frame == len(self.images) - 1:
                    self.done = True
    
    # Returns the current frame
    def img(self):
        return self.images[self.frame]
    
# Loads an image using its location   
def load_image(path):
    img = pygame.image.load(path).convert_alpha()
    return img
    
# Loads a group of images in a directory
def load_images(path):
    images = []
    for img_name in sorted(os.listdir(path)):
        img_path = os.path.join(path, img_name)
        if os.path.isfile(img_path):
            img = load_image(img_path)
            if img:
                images.append(img)
    return images

def load_animations(base_path, data="data/animation_data.json"):
    assets = {}
    with open(data, "rb") as file:
        data = json.load(file)
    
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            relative_path = os.path.relpath(dir_path, base_path).replace("\\", "/")
            logger.info("Loading animations from directory: %s", dir_path)  # Debug info
            if relative_path in data:
                assets[relative_path] = Animation(load_images(dir_path), data[relative_path]["img_dur"], data[relative_path]["loop"])
            else:
                assets[relative_path] = Animation(load_images(dir_path))
    
    logger.debug("Animation keys added: %s", assets.keys())  # 
    return assets