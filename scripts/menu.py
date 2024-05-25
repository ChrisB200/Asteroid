import pygame
from pygame.constants import *
import logging

logger = logging.getLogger(__name__)

class UserInterface:
    def __init__(self, resolution):
        self.menus = []
        self.screen = pygame.Surface(resolution, pygame.SRCALPHA | pygame.HWSURFACE)
        self.currentMenus = []

    def update(self):
        for menu in self.menus:
            menu.update()
        self.get_hover()

    def draw(self):
        self.screen.fill((0, 0, 0, 0))  # Clear the screen with transparency
        for menu in sorted(self.menus, key=lambda menu: menu.uiLayer):
            if menu.visible:
                menu.draw(self.screen)

    def get_hover(self):
        hoverElements = []
        for menu in self.menus:
            for element in menu:
                if element.rect.collidepoint(pygame.mouse.get_pos()):
                    hoverElements.append(element)
                    print("yes king")

        for hoveredElement in sorted(hoverElements, key=lambda hoveredElement: hoveredElement.uiLayer):
            hoveredElement.hover = True
            print(f"{hoveredElement.name}, Hovering")

    def add_menu(self, child):
        self.menus.append(child)

    def remove_menu(self, child):
        self.menus.pop(child, None)

class Menu(pygame.sprite.Group):
    def __init__(self, name, transform, size, uiLayer=1):
        super().__init__()
        self.name = name
        self.transform = pygame.math.Vector2(transform)
        self.size = size
        self.surface = pygame.Surface(size, pygame.SRCALPHA | pygame.HWSURFACE)
        self.uiLayer = uiLayer
        self.active = False
        self.visible = True

    def draw(self, screen):
        self.surface.fill((0, 0, 0, 0))  # Clear the surface with transparency
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.uiLayer):
            transform = sprite.globalTransform(self.transform)
            self.surface.blit(sprite.image, transform)
            sprite.rect.x, sprite.rect.y = transform.x + sprite.rect.width//4, transform.y + sprite.rect.height
        screen.blit(self.surface, self.transform)

class Element(pygame.sprite.Sprite):
    def __init__(self, name, transform, image, text=None, uiLayer=1):
        super().__init__()
        self.name = name
        self.transform = pygame.math.Vector2(transform)
        self.image = image
        self.text = text
        self.rect = self.image.get_rect(topleft=transform)
        self.uiLayer = uiLayer
        self.hover = True
        self.visible = True

    def update(self):
        pass

    def globalTransform(self, menuTransform):
        return self.transform + menuTransform

    def event_handler(self, event):
        pass

# Example usage:
pygame.init()
resolution = (800, 600)
ui = UserInterface(resolution)

window = pygame.display.set_mode(resolution)

menu = Menu('main_menu', (50, 50), (700, 500))

button_image = pygame.Surface((200, 50))
button_image.fill((255, 0, 0))
button = Element('button', (100, 100), button_image, "Button", 1)

button_image2 = pygame.Surface((200, 100))
button_image2.fill((0, 255, 0))
button2 = Element('button2', (200, 150), button_image2, "Button2", 2)

button_image3 = pygame.Surface((100, 200))
button_image3.fill((0, 0, 255))
button3 = Element('button3', (300, 200), button_image3, "Button3", 3)

menu.add(button3, button2, button)
ui.add_menu(menu)

clock = pygame.time.Clock()

# Main loop
running = False
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == K_RIGHT:
                menu.transform.x += 10
            if event.key == K_LEFT:
                menu.transform.x -= 10
    
    window.fill((100, 100, 100))
    ui.update()
    ui.draw()
    pygame.draw.rect(window, (255, 255, 0), button.rect)
    window.blit(ui.screen, (0, 0))
    pygame.display.flip()

pygame.quit()
