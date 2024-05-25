# Modules
import pygame
from pygame.constants import *
import logging

# Scripts
from scripts.menu import UserInterface, Menu, Element

logger = logging.getLogger(__name__)
    
class Window():
    """
    A class that manages the drawing of the window. This allows for pixel art to be easily upscaled. This class has 2 cameras. A world camera and a foreground camera. The world camera should be for entities in the world which are affected by scale. The foreground camera should be for elements like the cursor.
    """
    def __init__(self, resolution, flags=pygame.FULLSCREEN):
        self.resolution = resolution
        self.display = pygame.display.set_mode(resolution, flags=flags)

        self.world = Camera(self.resolution, 3, (0, 0), minScale=1, maxScale=1, panStrength=10)
        self.foreground = Camera(self.resolution, 1)
        self.ui = UserInterface(self.resolution)
    
    @property
    def worldScreen(self):
        return self.world.screen
    
    @property
    def foregroundScreen(self):
        return self.foreground.screen
    
    def update(self):
        self.world.update()
        self.foreground.update()

    def draw_world(self, *args, **kwargs):
        self.world.draw(*args, **kwargs)

    def draw_foreground(self, *args, **kwargs):
        self.foreground.draw(*args, **kwargs)

    def draw_ui(self):
        self.ui.draw()

    def draw(self):
        self.display.fill((0, 0, 0))
        self.display.blit(pygame.transform.scale(self.worldScreen, self.resolution), self.world.scrollDiff)
        self.display.blit(self.foregroundScreen, (0, 0))
        self.display.blit(self.ui.screen, (0, 0))

class Camera(pygame.sprite.Group):
    def __init__(self, resolution, scale, offset=(0, 0), panStrength=20, minScale=1, maxScale=1, zoomSpeed=1):
        super().__init__(self)
        self.resolution = resolution
        self.scale = scale
        self.offset = offset
        self.screen = pygame.Surface((self.resolution[0] / self.scale, self.resolution[1] / self.scale), pygame.SRCALPHA | pygame.HWSURFACE)
        # scroll
        self.trueScroll = pygame.math.Vector2()
        self.oldScroll = pygame.math.Vector2()
        self.scrollDiff = pygame.math.Vector2()
        # tracking
        self.target = None  # [target, [offsetX, offsetY]]
        self.isPanning = False
        self.panStrength = panStrength
        # scaling
        self.desiredScale = scale
        self.minScale = scale - minScale
        self.maxScale = scale + maxScale
        self.zoomSpeed = zoomSpeed
        # other
        self.renderOrder = {"x": False, "y": False, "layer": True}
        self.targets = ()
        self.queue = []

    @property
    def scroll(self):
        scroll = pygame.math.Vector2(int(self.trueScroll.x), int(self.trueScroll.y))
        self.scrollDiff = scroll - self.trueScroll
        return scroll
    
    # the rescaled screen size
    @property
    def screenSize(self):
        return self.screen.get_size()[0], self.screen.get_size()[1]
    
    def calculate_scroll(self, sprite):
        if sprite.isScroll:
            self.screen.blit(sprite.image, (sprite.transform.x - self.scroll.x, sprite.transform.y - self.scroll.y))
        else:
            self.screen.blit(sprite.image, (sprite.transform.x, sprite.transform.y))

    def draw_line(self, colour, start, end, width=1, layer=1):
        self.queue.append(("line", colour, start, end, width, layer))

    def draw_circle(self, colour, transform, radius, width=0, layer=1):
        self.queue.append(("circle", colour, transform, radius, width, layer))

    def draw_rect(self, colour, rect, layer=1):
        self.queue.append(("rect", colour, rect, layer))

    # draws the keyword arguments
    def draw_background(self, **kwargs):
        if "fill" in kwargs:
            self.screen.fill(kwargs["fill"])
        else:
            self.screen.fill((0, 0, 0, 0))  # fill with transparency by default

    def sort_sprites(self, sprite):
        if isinstance(sprite, tuple):
            return sprite[-1]
        else:
            return sprite.camLayer

    def draw_queue(self):
        sorted_queue = sorted(self.queue, key=lambda item: self.sort_sprites(item))
        
        for item in sorted_queue:
            if isinstance(item, tuple):
                match item[0]:
                    case "line":
                        pygame.draw.line(self.screen, item[1], item[2] - self.scroll, item[3] - self.scroll, item[4])
                        pygame.draw.circle(self.screen, (255, 0, 0), item[2] - self.scroll, 3)
                        pygame.draw.circle(self.screen, (0, 255, 0), item[3] - self.scroll, 3)
                    case "rect":
                        rect = item[2].copy()  # Assuming rect has a copy method or use `pygame.Rect` methods if it's a Rect
                        rect.x -= self.scroll.x
                        rect.y -= self.scroll.y
                        pygame.draw.rect(self.screen, item[1], rect)
                    case "circle":
                        pygame.draw.circle(self.screen, item[1], item[2] - self.scroll, item[3], item[4])
            else:
                self.calculate_scroll(item)

        # Clear the queue after processing
        self.queue.clear()


    # sets a target sprite
    def set_target(self, target, offset=(0, 0)):
        self.target = target
        self.offset = offset

    # sets multiple target sprites
    def set_targets(self, *args, offset=(0, 0)):
        self.targets = args
        self.offset = offset

    # follows the center of a target 
    def follow_target(self):
        targetCenter = pygame.math.Vector2()
        # slowly pans
        if self.isPanning:
            targetCenter.x = (self.target.transform.x + self.target.size[0] // 2) + self.offset[0]
            targetCenter.y = (self.target.transform.y + self.target.size[1] // 2) + self.offset[1]
            self.trueScroll.x += ((targetCenter.x - self.trueScroll.x) - self.screenSize[0] / 2) / self.panStrength
            self.trueScroll.y += ((targetCenter.y - self.trueScroll.y) - self.screenSize[1] / 2) / self.panStrength
        # instantly follows
        else:
            targetCenter.x = (self.target.transform.x + self.target.size[0] // 2)
            targetCenter.y = (self.target.transform.y + self.target.size[1] // 2)
            self.trueScroll.x += ((targetCenter.x - self.trueScroll.x) - self.screenSize[0] / 2) / self.panStrength
            self.trueScroll.y += ((targetCenter.y - self.trueScroll.y) - self.screenSize[1] / 2) / self.panStrength

    # follows the center of multiple targets
    def follow_multiple_targets(self):
        # Get values for bounding box of all targets
        boundingMin = pygame.math.Vector2()
        boundingMin.x = min(target.transform.x for target in self.targets) - 100
        boundingMin.y = min(target.transform.y for target in self.targets) - 100

        boundingMax = pygame.math.Vector2()
        boundingMax.x = max(target.transform.x + target.width for target in self.targets) + 100
        boundingMax.y = max(target.transform.y + target.height for target in self.targets) + 100

        # calculate the size of the bounding box
        boxWidth = boundingMax.x - boundingMin.x
        boxHeight = boundingMax.y - boundingMin.y

        # calculate the required scale to fit the bounding box on the screen
        requiredScale = pygame.math.Vector2(self.resolution[0] / boxWidth, self.resolution[1] / boxHeight)
        minRequiredScale = min(requiredScale.x, requiredScale.y)

        # calculate the current distance between targets
        currentDistance = boundingMax - boundingMin

        # check if targets are moving away from each other
        if (currentDistance.x > boxWidth // requiredScale.x) or (currentDistance.y > boxHeight // requiredScale.y):
            # update the camera scale to fit the bounding box
            self.zoom(minRequiredScale - self.scale)
        else:
            # zoom back in towards the initial scale
            self.zoom(self.scale - self.scale)  # Equivalent to self.zoom(0)

        # center the camera on the center of the bounding box
        center = (boundingMin + boundingMax) / 2
        targetCenter = pygame.math.Vector2()
        targetCenter.x = center.x + self.offset[0]
        targetCenter.y = center.y + self.offset[1]

        self.trueScroll.x += ((targetCenter.x - self.trueScroll.x) - self.screenSize[0] / 2) / self.panStrength
        self.trueScroll.y += ((targetCenter.y - self.trueScroll.y) - self.screenSize[1] / 2) / self.panStrength

    # allows for zooming functionality
    def zoom(self, amount: float):
        # incrementally update the desired scale
        self.desiredScale += amount
        # clamp the desired scale to the defined range
        self.desiredScale = max(self.minScale, min(self.maxScale, self.desiredScale))
        # smoothly transition the current scale towards the desired scale
        self.scale += (self.desiredScale - self.scale) * self.zoomSpeed
        tempScreen = pygame.transform.scale(self.screen.copy(), (self.resolution[0] / self.scale, self.resolution[1] / self.scale))
        self.screen = tempScreen

    # handles all the drawing within the camera class
    def draw(self, **kwargs):
        self.draw_background(**kwargs)

        for sprite in self.sprites():
            self.queue.append(sprite)

        self.draw_queue()

    # handles all the updates within the camera class
    def update(self):
        if self.targets:
            self.follow_multiple_targets()
        elif self.target is not None:
            self.follow_target()
