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
        self.fitToSize = True

        # animation
        self.action: str = ""
        self.anim_offset: tuple[int, int] = (0, 0)
        self.anim = animation

        self.set_action(self.anim)

    def get_center(self):
        x = self.transform.x + (self.size[0] // 2)
        y = self.transform.y + (self.size[1] // 2)
        return pygame.math.Vector2(x, y)

    @property
    def image(self):
        image = self.animation.img()
        if not self.fitToSize:
            image = pygame.transform.scale(image, self.size)
        else:
            # Get original dimensions
            original_width, original_height = image.get_size()
            target_width, target_height = self.size

            # Calculate the scaling factor to maintain aspect ratio
            width_ratio = target_width / original_width
            height_ratio = target_height / original_height
            scaling_factor = min(width_ratio, height_ratio)

            # Calculate the new dimensions
            new_width = int(original_width * scaling_factor)
            new_height = int(original_height * scaling_factor)

            # Scale the image to the new dimensions
            scaled_image = pygame.transform.scale(image, (new_width, new_height))

            # Create a new surface with the target size and transparent background
            centered_image = pygame.Surface((target_width, target_height), pygame.SRCALPHA)

            # Calculate the top-left position to blit the scaled image
            top_left_x = (target_width - new_width) // 2
            top_left_y = (target_height - new_height) // 2

            # Blit the scaled image onto the centered image surface
            centered_image.blit(scaled_image, (top_left_x, top_left_y))

            image = centered_image

        image = pygame.transform.rotate(pygame.transform.flip(image, self.flip, False), self.rotation).convert_alpha()

        return image

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
