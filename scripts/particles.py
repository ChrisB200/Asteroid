import random, pygame
from pygame.locals import *

from scripts.lighting import circle_surf
from scripts.framework import get_center

class Particle():
    def __init__(self, transform, velocity, timer, radius, shrinkvel, gravity=False, layer=0, gravityStrength=0, colour=(255, 255, 255), lighting=False, lightingCol=(255, 255, 255)):
        self.transform = pygame.math.Vector2(transform)
        self.velocity = pygame.math.Vector2(velocity)
        self.timer = timer
        self.radius = radius
        self.shrinkvel = random.randrange(int(shrinkvel*100 - 2), int(shrinkvel*100))/100
        self.gravity = gravity
        self.colour = colour
        self.lighting = lighting
        self.lightingCol = lightingCol
        self.lightingRadius = self.timer * 1.5
        self.gravityStrength = gravityStrength
        self.remove = False
        self.layer = layer

    def draw(self, camera):
        camera.draw_circle(self.colour, self.transform, self.radius, layer=self.layer)

        if self.lighting:
            lighting = circle_surf(self.lightingRadius, self.lightingCol)
            lighting_transform = self.transform.copy()
            lighting_transform.x -= self.lightingRadius
            camera.draw_surface(lighting, lighting_transform, BLEND_RGB_ADD, 20)

    def update(self, dt):
        movement = pygame.math.Vector2(self.velocity.x * dt, self.velocity.y * dt)
        self.transform += movement
        self.radius -= self.shrinkvel * dt

        if self.gravity == True:
            self.transform.y += self.gravityStrength
        if self.radius <= 0:
            self.remove = True
        if self.lighting:
            self.lightingRadius = self.timer * 1.5
        

class ParticleSystem():
    def __init__(self, transform, transformOffset=(0, 0), *args):
        self.transform = transform
        self.transformOffset = pygame.math.Vector2(transformOffset)
        self.particles = [*args]

    def add(self, *particles):
        for particle in particles:
            self.particles.append(particle)

    def update(self, dt, transform=None):
        for particle in self.particles:
            particle.update(dt)

        for count, particle in sorted(enumerate(self.particles), reverse=True):
            if particle.remove:
                self.particles.pop(count)

        if transform:
            self.transform = transform + self.transformOffset

    def draw(self, camera):
        for particle in self.particles:
            particle.draw(camera)