import random, pygame
from pygame.locals import *

class Particle():
    def __init__(self, transform, velocity, radius, shrinkvel, gravity=False, layer=0, gravityStrength=0, colour=(255, 255, 255)):
        self.transform = pygame.math.Vector2(transform)
        self.velocity = pygame.math.Vector2(velocity)
        self.radius = radius
        self.shrinkvel = random.randrange(int(shrinkvel*100 - 2), int(shrinkvel*100))/100
        self.gravity = gravity
        self.colour = colour
        self.gravityStrength = gravityStrength
        self.remove = False
        self.layer = layer

    def draw(self, camera):
        camera.draw_circle(self.colour, self.transform, self.radius, self.layer)

    def update(self, dt):
        movement = pygame.math.Vector2(self.velocity.x * dt, self.velocity.y * dt)
        self.transform += movement
        self.radius -= self.shrinkvel * dt

        if self.gravity == True:
            self.transform.y += self.gravityStrength
        if self.radius <= 0:
            self.remove = True

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