import pygame
from pygame.constants import *

from scripts.entities import PhysicsEntity
from scripts.particles import Particle, ParticleSystem

class Weapon():
    def __init__(self, maxMagazine, reloadTime, isAutomatic, shootTime, bullet, muzzleAreas):
        # magazine
        self.maxMagazine = maxMagazine
        self.magazine = self.maxMagazine
        self.reloadTime = reloadTime
        self.currentReloadTime = 0
        self.canReload = True
        self.isAutomatic = isAutomatic

        # time between shots
        self.shootTime = shootTime
        self.currentShootTime = 0
        self.canShoot = True
        self.shooting = False

        self.bullet = bullet
        self.muzzleAreas = muzzleAreas

    def copy(self):
        return self.__class__(self.maxMagazine, self.reloadTime, self.isAutomatic, self.shootTime, self.bullet, self.muzzleAreas)

    def calculate_muzzle_areas(self, transform):
        muzzleTransforms = []
        for muzzle in self.muzzleAreas:
            print(muzzle)
            muzzleTransforms.append((transform.x + muzzle[0], transform.y + muzzle[1]))
        return muzzleTransforms
    
    # shoot bullets
    def shoot(self, game, transform):
        if self.canShoot and self.magazine > 0:
            muzzleTransforms = self.calculate_muzzle_areas(transform)
            for muzzle in muzzleTransforms:
                # create bullet at muzzle transform
                bullet = self.bullet.copy()
                bullet.start(muzzle)
                # add to world and camera
                game.projectiles.add(bullet)
                game.add_to_world(bullet)

            # start timer
            self.currentShootTime = self.shootTime
            self.magazine -= 1

    def reload(self):
        if self.canReload: self.currentReloadTime = self.reloadTime

    def update_timers(self, dt):
        # reload time
        if self.currentReloadTime <= 0:
            if self.canReload == False:#
                self.magazine = self.maxMagazine
            self.canReload = True
            self.localRotation = 0
            # time between shots timer
            if self.currentShootTime <= 0 and self.currentReloadTime <=0:
                self.canShoot = True
            elif self.currentShootTime > 0:
                self.currentShootTime -= 1 * dt
                self.canShoot = False
            else:
                self.canShoot = False
        elif self.currentReloadTime > 0:
            self.currentReloadTime -= 1 * dt
            self.canReload = False
            self.canShoot = False

    def update(self, game, transform):
        self.update_timers(game.dt)
        # fully automatic shooting
        if self.shooting: self.shoot(game, transform)        

class Projectile(PhysicsEntity):
    def __init__(self, transform, size, tag, assets, layer=0, isScroll=True, animation="idle"):
        super().__init__(transform, size, tag, assets, layer, isScroll, animation)
        self.damage = 25
        self.movement.y = -1
        self.speed = 350
        self.hit = False
        self.set_rotation(-90)
        self.canDoDamage = True
        self.asteroid = None
        self.particles = ParticleSystem(self.transform)

    def copy(self):
        return self.__class__(self.transform, self.size, self.tag, self.assets, self.camLayer, self.isScroll, self.anim)

    def start(self, transform):
        self.transform = pygame.math.Vector2(transform)

    def check_finished(self):
        if self.hit:
            if self.animation.done:
                self.kill()
        if self.asteroid:
            self.asteroid.asteroid_particles(self.transform, self.particles)

    def hit_entity(self, sprite):
        if self.canDoDamage:
            self.movement.y = 0
            self.set_action("hit")
            self.hit = True
            self.canDoDamage = False   

    def handle_collision(self, sprite):
        if sprite.tag == "asteroid":
            self.hit_entity(sprite)
            self.asteroid = sprite
        if sprite.tag == "ufo":
            self.hit_entity(sprite)

        super().handle_collision(sprite)

    def update(self, dt, game):
        self.update_animation(dt)
        self.move(self.movement * self.speed, [], dt)
        self.check_collisions(game.asteroids, game.ufos)
        self.check_finished()
        self.particles.update(dt, self.transform)
        self.particles.draw(game.window.world)
