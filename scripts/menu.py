import pygame
from pygame.constants import *

class Element():
    def __init__(self, transform, size):
        self.transform = pygame.math.Vector2(transform)
        self.localTransform = self.transform.copy()
        self.size = size
        self.layer = 1
        self.active = False
        self.hasPressed = False
        self.visible = True

    def set_visible(self, state):
        self.visible = state

    def set_active(self, state):
        self.active = state

    def set_transform(self, x=None, y=None):
        if self.transform != self.localTransform:
            if x:
                self.localTransform.x = x
            if y:
                self.localTransform.y = y
        else:
            if x:
                self.localTransform.x = x
            if y:
                self.localTransform.y = y
            self.transform = self.localTransform.copy()

    def dock(self, size, x, y):
        if x:
            self.set_transform(size[0] // 2 - (self.size[0] // 2))
        if y:
            self.set_transform(size[1] // 2 - (self.size[1] // 2))

    def update(self, dt):
        pass

class SurfaceElement(Element):
    def __init__(self, transform, size, surface):
        super().__init__(transform, size)
        self.surface = surface

    @property
    def image(self):
        return self.surface

class RectElement(Element):
    def __init__(self, transform, size, colour):
        super().__init__(transform, size)
        self.colour = colour
        self.rect = pygame.Rect(self.transform.x, self.transform.y, size[0], size[1])
        self.surface = pygame.Surface(size, pygame.SRCALPHA)

    @property
    def image(self):
        pygame.draw.rect(self.surface, self.colour, self.rect)
        return self.surface

class AnimatedElement(Element):
    def __init__(self, transform, size, tag, assets, animation="idle"):
        super().__init__(transform, size)
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
         font = self.font.render(self.text, False, self.colour)
         font.convert_alpha()
         self.size = (font.get_width(), font.get_height())
         return font
    
    def center_text_x(self, screenSize):
        self.transform.x = (screenSize[0] // 2) - (self.image.get_width() // 2)

    def center_text_y(self, screenSize):
        self.transform.y = (screenSize[1] // 2) - (self.image.get_height() // 2)
    
    def change_text(self, text):
        self.text = text

    def change_colour(self, colour):
        self.colour = colour

    def change_font(self, font):
        self.font = font
    
    def update(self, dt):
        self.size = self.image.get_width(), self.image.get_height()

class Group(Element):
    def __init__(self, transform, size, *elements):
        super().__init__(transform, size)
        self.add(*elements)
        self.elements = []

    @property
    def image(self):
        return pygame.Surface((0, 0))

    def add(self, *elements):
        for element in elements:
            self.elements.append(element)

    def set_visbile(self, state):
        for element in self.elements:
            element.set_visible(state)

    def set_active(self, state):
        for element in self.elements:
            element.set_active(state)

    def center_element_x(self, element):
        x = self.transform.x + ((element.size[0] // 2) - (self.size[0] // 2))
        element.set_transform(x, None)

    def center_element_y(self, element):
        y = self.transform.y + (self.size[1] // 2 - (element.size[1] // 2))
        element.set_transform(None, y)
        
    def update(self, dt):
        for element in self.elements:
            element.update(dt)
            element.transform = self.transform + element.localTransform

class UserInterface():
    def __init__(self, size):
        self.transform = pygame.math.Vector2()
        self.size = size
        self.elements = []
        self.surface = pygame.Surface(self.size, pygame.SRCALPHA | pygame.HWSURFACE)
        self.hoveredElements = []

    def add(self, *elements):
        for element in elements:
            self.elements.append(element)

    def add_group(self, *groups):
        for group in groups:
            self.add(group, *group.elements)

    def remove(self, *elements):
        for element in elements:
            self.elements.remove(element)

    def update(self, dt, camera):
        if self.hoveredElements == []:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        mx, my = pygame.mouse.get_pos()[0] // camera.scale, pygame.mouse.get_pos()[1] // camera.scale
        for element in self.elements:
            element.update(dt)
            
            if element.active:
                if mx > element.transform.x and mx < element.transform.x + element.size[0]:
                    if my < element.transform.y + element.size[1] and my > element.transform.y:
                        pygame.mouse.set_visible(True)
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                    
                        if element not in self.hoveredElements:
                            self.hoveredElements.append(element)
                    else:
                        if element in self.hoveredElements:
                            self.hoveredElements.remove(element)

    def draw(self):
        self.surface.fill((0, 0, 0, 0))
        for element in sorted(self.elements, key=lambda element: element.layer):
            if element.visible:
                self.surface.blit(element.image, (element.transform.x, element.transform.y))
