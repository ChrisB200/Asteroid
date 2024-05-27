import pygame
from pygame.constants import *

class Element():
    def __init__(self, transform, size):
        self.transform = pygame.math.Vector2(transform)
        self.size = size
        self.layer = 1

    def update(dt):
        pass

class AnimatedElement(Element):
    def __init__(self, transform, size, tag, assets, animation="idle"):
        super().__init__(transform, size)
        self.transform = pygame.math.Vector2(transform)
        self.size = size
        self.tag = tag
        self.assets = assets
        self.rotation = 0
        self.flip = False

        # animation
        self.action: str = ""
        self.anim_offset: tuple[int, int] = (0, 0)
        self.anim = animation

        self.set_action(self.anim)

    @property
    def image(self):
        return pygame.transform.rotate(pygame.transform.flip(self.animation.img(), self.flip, False), self.rotation).convert_alpha()

    def change_tag(self, tag, action="idle"):
        self.tag = tag
        self.set_action(action, True)

    # sets an animation action
    def set_action(self, action, override=False):
        if action != self.action or override:
            self.action = action
            self.animation = self.assets[self.tag + "/" + self.action].copy()

    # updates the current frame of an animation
    def update_animation(self, dt):
        self.animation.update(dt)

    def update(self, dt):
        self.update_animation(dt)

class TextElement(Element):
    def __init__(self, transform, text, font, colour=(255, 255, 255)):
        super().__init__(transform, (0, 0))
        self.text = text
        self.font = font
        self.colour = colour

    @property
    def image(self):
        return self.font.render(self.text, False, self.colour)
    
    def change_text(self, text):
        self.text = text

    def change_colour(self, colour):
        self.colour = colour

    def change_font(self, font):
        self.font = font
    
    def update(self, dt):
        self.size = self.image.get_width(), self.image.get_height()

class UserInterface():
    def __init__(self, size):
        self.transform = pygame.math.Vector2()
        self.size = size
        self.elements = []
        self.surface = pygame.Surface(self.size, pygame.SRCALPHA | pygame.HWSURFACE)

    def add(self, *elements):
        for element in elements:
            self.elements.append(element)

    def remove(self, *elements):
        for element in elements:
            self.elements.remove(element)

    def update(self, dt):
        for element in self.elements:
            element.update(dt)

    def draw(self):
        self.surface.fill((0, 0, 0, 0))
        for element in sorted(self.elements, key=lambda element: element.layer):
            self.surface.blit(element.image, (element.transform.x, element.transform.y))
