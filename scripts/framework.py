# Modules
import pygame
from pygame.constants import *

import logging

logger = logging.getLogger(__name__)

MENU = 0
PLAYING = 1
PAUSED = 2

# Returns a crop of a selected surface
def clip(surf, x1, y1, x2, y2):
    clip = pygame.Rect(x1, y1, x2, y2)
    img = surf.subsurface(clip)
    return img

# Rotates an image arount a pivot position
def blit_rotate(image, pos, originPos, angle):
    image_rect = image.get_rect(topleft = (pos.x - originPos.x, pos.y - originPos.y))
    offset_center_to_pivot = pygame.math.Vector2(pos) - image_rect.center
    rotated_offset = offset_center_to_pivot.rotate(-angle)
    rotated_image_center = (pos.x - rotated_offset.x, pos.y - rotated_offset.y)
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center = rotated_image_center)
    return (rotated_image, rotated_image_rect)

# Removes case sensitivity from string comparisons
def convertBool(val):
    return True if val.lower() == "true" else False

# Returns centered coordinates of surface
def blit_center(display, pos):
    x = int(display.get_width() / 2)
    y = int(display.get_height() / 2)
    return (pos[0] - x, pos[1] - y)

# returns center of something
def get_center(pos, size):
    x = pos.x + int(size[0] / 2)
    y = pos.y + int(size[1] / 2)
    return pygame.math.Vector2(x, y)

# Flips an image
def flip_img(img,boolean=True, boolean_2=False):
    return pygame.transform.flip(img,boolean,boolean_2)

# Caps a number to be below a target
def numCap(number, target):
    if target >= 0:
        if number > target:
            return target
        else:
            return number
    else:
        if number < target:
            return target
        else:
            return number

# Checks for collisions between 2 objects   
def collision_test(object_1,object_list):
    collision_list = []
    for obj in object_list:
        if obj.colliderect(object_1):
            collision_list.append(obj)
    return collision_list

# Sets an objects position to another position
def setPos(object, pos):
    object.pos[0] = pos[0]
    object.pos[1] = pos[1]

# Splits a .csv file into a 2D array
def load_map(filename):
    grid = []
    with open(filename) as map:
        for row in map:
            rows = row.split(",")
            grid.append(rows)
    for count, row in enumerate(grid):
        temp = grid[count][len(row)-1].split("\n")
        grid[count][len(row)-1] = temp[0]
    return grid

# Resets value to 0 if goes over a specific index
def looping(list, index, increment):
    length = len(list) - 1
    if index + increment > length:
        return 0
    elif index + increment < length:
        return length
    else:
        return index + increment