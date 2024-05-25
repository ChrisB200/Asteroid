# Modules
import pygame
import random
import math
import logging
from pygame.constants import *

# Scripts
from scripts.framework import get_center, collision_test
from scripts.input import Controller, Keyboard
from scripts.animation import Animation
from scripts.camera import Camera
from scripts.particles import Particle, ParticleSystem

logger = logging.getLogger(__name__)

class ModifiedSpriteGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

    def get_entity(self, index):
        return self.sprites()[index]

class Entity(pygame.sprite.Sprite):
    def __init__(self, transform:tuple[int, int], size:tuple[int, int], tag:str, assets:dict[str, Animation], camLayer=0, isScroll=True, animation="idle"):
        super().__init__()
        # parameters
        self.transform = pygame.math.Vector2(transform)
        self.size = size
        self.tag = tag
        self.assets = assets
        self.camLayer = camLayer
        self.isScroll = isScroll
        self.rotation = 0

        # movement
        self.flip = False
        self.directions: dict[str, bool] = {"left" : False, "right": False, "up": False, "down": False}
        self.movement = pygame.math.Vector2()
        self.speed = 100
        
        # animation
        self.action: str = ""
        self.anim_offset: tuple[int, int] = (0, 0)
        self.anim = animation

        self.set_action(self.anim)
        
        self.rect: pygame.Rect = pygame.Rect(self.transform.x, self.transform.y, self.size[0], self.size[1])
    
    @property
    def width(self):
        return self.size[0]
    
    @property
    def height(self):
        return self.size[1]
    
    @property
    def image(self):
        return pygame.transform.rotate(pygame.transform.flip(self.animation.img(), self.flip, False), self.rotation).convert_alpha()

    # sets an animation action
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.assets[self.tag + "/" + self.action].copy()

    def calculate_direction(self) -> pygame.math.Vector2:
        direction = pygame.math.Vector2()
        direction.x = math.cos(math.radians(self.rotation)) 
        direction.y = -math.sin(math.radians(self.rotation))
        direction = direction.normalize()
        return direction

    # sets a transform
    def set_transform(self, transform):
        self.transform = pygame.math.Vector2(transform)
        self.rect.x = self.transform.x
        self.rect.y = self.transform.y

    # sets a rotation
    def set_rotation(self, rotation):
        self.rotation = rotation

    # updates the current frame of an animation
    def update_animation(self, dt):
        self.animation.update(dt)

    # gets the center of the entity
    def get_center(self):
        x = self.transform.x + (self.width // 2)
        y = self.transform.y + (self.height // 2)
        return pygame.math.Vector2(x, y)
    
    # changes the camera layer
    def change_layer(self, increment):
        self.camLayer += increment
    
    # gets the angle between 2 entities
    def get_entity_angle(self, entity_2):
        x1 = self.transform.x + int(self.width / 2)
        y1 = self.transform.y + int(self.height / 2)
        x2 = entity_2.x + int(entity_2.width / 2)
        y2 = entity_2.y + int(entity_2.height / 2)
        angle = math.atan((y2-y1) / (x2-x1))
        if x2 < x1:
            angle += math.pi
        return angle
    
    # gets the angle between an entity and a point
    def get_point_angle(self, point, scroll=pygame.math.Vector2(), offset=0, centered=False):
        transform = self.transform - scroll
        if centered:
            transform = self.get_center()
        radians = math.atan2(point.y - transform.y, point.x - transform.x)
        return -math.degrees(radians) + offset
    
    # gets the distance between an entity and a point
    def get_distance(self, point):
        dis_x = point[0] - self.get_center()[0]
        dis_y = point[1] - self.get_center()[1]
        return math.sqrt(dis_x ** 2 + dis_y ** 2)
    
    def update(self, dt):
        self.update_animation(dt)
        self.rect.x = self.transform.x
        self.rect.y = self.transform.y
    
class PhysicsEntity(Entity):
    def __init__(self, transform:tuple[int, int], size:tuple[int, int], tag:str, assets:dict[str, Animation], layer=0, isScroll=True, animation="idle"):
        # Parameters
        super().__init__(transform, size, tag, assets, layer, isScroll, animation)
        # Rects and Collisions
        self.collisions: dict[str, bool] = {'bottom': False, 'top': False, 'left': False, 'right': False}

    # Checks for collisions based on movement direction
    def move(self, movement, tiles, dt):
        # x-axis
        self.transform.x += movement[0] * dt
        self.rect.x = self.transform.x
        tileCollisions = collision_test(self.rect, tiles)
        objectCollisions = {'bottom': False, 'top': False, 'left': False, 'right': False}
        for tile in tileCollisions:
            if movement[0] > 0:
                self.rect.right = tile.left
                objectCollisions["right"] = True
            elif movement[0] < 0:
                self.rect.left = tile.right
                objectCollisions["left"] = True
        self.transform.x = int(self.rect.x)

        # y-axis
        self.transform.y += movement[1] * dt
        self.rect.y = self.transform.y
        tileCollisions = collision_test(self.rect, tiles)
        for tile in tileCollisions:
            if movement[1] > 0:
                self.rect.bottom = tile.top
                objectCollisions["bottom"] = True
            elif movement[1] < 0:
                self.rect.top = tile.bottom
                objectCollisions["top"] = True
        self.transform.y = int(self.rect.y)
        self.collisions = objectCollisions

class Player(PhysicsEntity):
    def __init__(self, id:int, transform:tuple[int, int], size:tuple[int, int], tag:str, assets:dict[str, Animation], layer=0, isScroll=True, animation="idle"):
        super().__init__(transform, size, tag, assets, layer, isScroll, animation)
        self.id = id
        self.speed = 150
        self.weapon = None
        self.directions = {"up": False, "down": False, "left": False, "right": False}
        self.input = None

        center = self.get_center()
        center.y += 10
        self.particles = ParticleSystem(self.transform, (16.5, 26))
        self.set_action("idle")

    def event_handler(self, event, game):
        if self.input is not None:
            if isinstance(self.input, Controller):
                self.controller_input(event, game)
            else:
                self.keyboard_input(event, game)

    def keyboard_input(self, event, game):
        if event.type == pygame.KEYDOWN:
            if event.key == self.input.controls.moveLeft:
                self.directions["left"] = True
            if event.key == self.input.controls.moveRight:
                self.directions["right"] = True
            if event.key == self.input.controls.moveUp:
                self.directions["up"] = True
            if event.key == self.input.controls.moveDown:
                self.directions["down"] = True
            if event.key == self.input.controls.reload:
                if self.weapon:
                    self.weapon.reload()

        elif event.type == pygame.KEYUP:
            if event.key == self.input.controls.moveLeft:
                self.directions["left"] = False
            if event.key == self.input.controls.moveRight:
                self.directions["right"] = False
            if event.key == self.input.controls.moveUp:
                self.directions["up"] = False
            if event.key == self.input.controls.moveDown:
                self.directions["down"] = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == self.input.controls.shoot:
                if self.weapon:
                    if self.weapon.isAutomatic:
                        self.weapon.shooting = True
                    else:
                        self.weapon.shoot(game)

        if event.type == pygame.MOUSEBUTTONUP:
            if self.weapon:
                if self.weapon.isAutomatic:
                    self.weapon.shooting = False

    def controller_input(self, event, game):
        if self.input.leftStick.x > 0:
            self.directions["right"] = True
            self.directions["left"] = False
        elif self.input.leftStick.x < 0:
            self.directions["left"] = True
            self.directions["right"] = False
        else:
            self.directions["left"] = False
            self.directions["right"] = False

        if self.input.leftStick.y > 0:
            self.directions["down"] = True
            self.directions["up"] = False
        elif self.input.leftStick.y < 0:
            self.directions["up"] = True
            self.directions["down"] = False
        else:
            self.directions["down"] = False
            self.directions["up"] = False

    def update_animation_state(self):
        pass

    def update_particles(self, dt, camera, transform=None):
        yellow = Particle(
            transform=self.particles.transform, 
            velocity=(random.randint(-150, 150) / 10, 40),
            radius=2, 
            shrinkvel=1.5, 
            colour=(255, 255, 0),
            layer=0
        )

        red = Particle(
            transform=self.particles.transform, 
            velocity=(random.randint(-150, 150) / 10, 40),
            radius=3, 
            shrinkvel=4, 
            colour=(255, 100, 0),
            layer=0
        )

        orange = Particle(
            transform=self.particles.transform, 
            velocity=(random.randint(-150, 150) / 10, 40),
            radius=2.5, 
            shrinkvel=2.5, 
            colour=(255, 200, 0),
            layer=0
        )

        #red = Particle(self.particles.transform, (random.randint(0, 20) / 10 -1, random.randint(4, 6)), 6, 0.75, False, 0.3, (255, 200, 0))
        #orange = Particle(self.particles.transform, (random.randint(0, 20) / 10 -1, random.randint(4, 6)), 6, 0.75, False, 0.3, (255, 100, 0))
        self.particles.add(yellow, red, orange)
        self.particles.update(dt, transform)
        self.particles.draw(camera)

    def update(self, tiles, dt, camera: Camera, game):
        self.movement.x = (-1 if self.directions["left"] else 1 if self.directions["right"] else 0) * self.speed
        self.movement.y = (-1 if self.directions["up"] else 1 if self.directions["down"] else 0) * self.speed

        if isinstance(self.input, Controller):
            self.movement = self.input.leftStick.copy() * self.speed

        if self.movement.length() > 0:
            self.movement.normalize()

        self.move(self.movement, tiles, dt)
        self.update_animation_state()
        self.update_animation(dt)
        self.update_particles(dt, camera, self.transform)

        if self.input:
            self.input.update()
        if self.weapon:
            self.weapon.update(self, camera, dt, game)
        #camera.draw_rect((255, 0, 0), self.rect)

class UserCursor(Entity):
    def __init__(self, transform, size, tag, assets, layer=0, isScroll=True):
        super().__init__(transform, size, tag, assets, layer, isScroll)
        self.location = pygame.math.Vector2(0, 0)

    def set_transform(self, x, y):
        self.transform.x = x
        self.transform.y = y

    def update(self, player:Player, camera:Camera, dt):
        x = self.transform.x
        y = self.transform.y
        if x < 0:
            x = 0
        elif x > camera.resolution[0]:
            x = camera.resolution[0]
        if y < 0:
            y = 0
        elif y > camera.resolution[1]:
            y = camera.resolution[1]

        
        if isinstance(player.input, Controller):
            x += round(player.input.rightStick[0] * 5)
            y += round(player.input.rightStick[1] * 5)
            self.transform.x = x
            self.transform.y = y
            self.set_transform(x, y)
        else:
            x, y = pygame.mouse.get_pos()
            self.set_transform(x, y)

        self.cursor_in_space(camera.scale)
        self.update_animation(dt)

    def cursor_in_space(self, camera_scale):
        self.location.x = self.transform.x // camera_scale
        self.location.y = self.transform.y // camera_scale

class UFO(PhysicsEntity):
    def __init__(self, transform, size, tag, assets, layer=1, isScroll=True):
        super().__init__(transform, size, tag, assets, layer, isScroll)
        self.arrow = Entity(transform, (32, 32), "arrow", assets, animation="enter")

    def spawn(self, screenSize):
        border = random.randint(1, 4)
        match border:
            case 1: # left
                amount = random.randint(100, screenSize[1] - 20)
                self.transform.x = self.width
                self.transform.y = amount
                direction = "right"
            case 2: # right
                amount = random.randint(100, screenSize[1] - 20)
                self.transform.x = screenSize[0] - self.width
                self.transform.y = amount
                direction = "left"
            case 3: # top
                amount = random.randint(20, screenSize[0] - 100)
                self.transform.x = amount
                self.transform.y = +self.height
                direction = "bottom"
            case 4: # bottom
                amount = random.randint(20, screenSize[0] - 100)
                self.transform.x = amount
                self.transform.y = screenSize[1] - self.height
                direction = "top"

        self.transform.x = self.transform.x - (self.width//2)
        self.transform.y = self.transform.y - (self.height//2)

        match direction:
            case "right":
                transform = self.get_center()
                transform.x += self.width
                self.arrow.set_transform(transform)
                self.arrow.set_rotation(0)
            case "left":
                transform = self.get_center()
                transform.x -= self.width
                self.arrow.set_transform(transform)
                self.arrow.set_rotation(180)
            case "top":
                transform = self.get_center()
                transform.y -= self.height
                self.arrow.set_transform(transform)
                self.arrow.set_rotation(90)
            case "bottom":
                transform = self.get_center()
                transform.y += self.height
                self.arrow.set_transform(transform)
                self.arrow.set_rotation(-90)
        self.arrow.set_action("enter")

    def update(self, dt, camera):
        self.update_animation(dt)
        self.rect.topleft = self.transform
        camera.draw_rect((255, 0, 0), self.rect, 10)