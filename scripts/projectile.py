import pygame
import random
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
        self.isReloading = False
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
            self.isReloading = False
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
            self.isReloading = True

    def update(self, game, transform):
        self.update_timers(game.dt)
        # fully automatic shooting
        if self.shooting: self.shoot(game, transform)    
        if self.magazine < self.maxMagazine: self.canReload == False    

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

    def check_bounds(self, resolution):
        if self.transform.y <= -25:
            self.kill()
        if self.transform.y >= resolution[1] + 25:
            self.kill ()
        if self.transform.x >= resolution[0] + 25:
            self.kill()
        if self.transform.x <= -25:
            self.kill()

    def handle_collision(self, sprite):
        if sprite.tag == "asteroid":
            self.hit_entity(sprite)
            self.asteroid = sprite
        if sprite.tag == "ufo":
            self.hit_entity(sprite)

        super().handle_collision(sprite)

    def update(self, dt, game, particles):
        self.update_animation(dt)
        self.move(self.movement * self.speed, [], dt)
        self.check_collisions(game.asteroids, game.ufos)
        self.check_finished()
        self.check_bounds(game.window.world.screenSize)
        self.particles.update(dt, self.transform)
        self.particles.draw(game.window.world)

class Missile(Projectile):
    def __init__(self, transform, size, tag, assets, layer=0, isScroll=True, animation="idle"):
        super().__init__(transform, size, tag, assets, layer, isScroll, animation)
        self.damage = 20
        self.particleOffset = pygame.math.Vector2(6, 10)
        self.set_rotation(0)
        self.explosionTimer = 0.5
        self.currentExplosionTimer = 0

    def hit_entity(self, sprite):
        if self.canDoDamage:
            self.movement.y = 0
            self.currentExplosionTimer = self.explosionTimer
            self.hit = True
            self.canDoDamage = False
            self.hide = True
    
    def update_timers(self, dt, particles):
        if self.currentExplosionTimer < 0 and self.hit == True:
            self.kill()
        if self.currentExplosionTimer > 0 and self.hit == True:
            self.currentExplosionTimer -= 1 * dt
            self.explosion_particles(particles)

    def explosion_particles(self, particles):
        speedMultiplier = 1.5

        white = Particle(
            transform=self.get_center(), 
            velocity=(random.randint(-150, 150) / speedMultiplier, random.randint(-150, 150) / speedMultiplier),
            timer = 2,
            radius=6, 
            shrinkvel=7, 
            colour=(255, 255, 255),
            layer=self.camLayer+2,
            lighting=True,
            lightingCol=(50, 50, 50)
        )

        red = Particle(
            transform=self.get_center(), 
            velocity=(random.randint(-150, 150) / speedMultiplier, random.randint(-150, 150) / speedMultiplier),
            timer = 2,
            radius=6, 
            shrinkvel=9, 
            colour=(255, 20, 0),
            layer=self.camLayer+2,
            lighting=True,
            lightingCol=(25, 10, 0)
        )

        orange = Particle(
            transform=self.get_center(), 
            velocity=(random.randint(-150, 150) / speedMultiplier, random.randint(-150, 150) / speedMultiplier),
            timer = 2,
            radius=6, 
            shrinkvel=8, 
            colour=(255, 100, 0),
            layer=self.camLayer+2,
            lighting=True,
            lightingCol=(25, 30, 0)
        )

        particles.add(white, red, orange)

    def booster_particles(self, particles):
        yellow = Particle(
            transform=self.particles.transform + self.particleOffset, 
            velocity=(random.randint(-150, 150) / 10, 40),
            timer = 2,
            radius=2, 
            shrinkvel=4, 
            colour=(255, 255, 0),
            layer=self.camLayer-1,
            lighting=True,
            lightingCol=(20, 20, 0)
        )

        red = Particle(
            transform=self.particles.transform + self.particleOffset, 
            velocity=(random.randint(-150, 150) / 10, 40),
            timer = 2,
            radius=3, 
            shrinkvel=4, 
            colour=(255, 100, 0),
            layer=self.camLayer-1,
            lighting=True,
            lightingCol=(25, 10, 0)
        )

        orange = Particle(
            transform=self.particles.transform + self.particleOffset, 
            velocity=(random.randint(-150, 150) / 10, 40),
            timer = 2,
            radius=2.5, 
            shrinkvel=2.5, 
            colour=(255, 200, 0),
            layer=self.camLayer-1,
            lighting=True,
            lightingCol=(25, 20, 0)
        )
        
        particles.add(yellow, red, orange)

    def update(self, dt, game, particles):
        super().update(dt, game, particles)
        self.booster_particles(particles)
        self.update_timers(dt, particles)

class PiercingProjectile(Projectile):
    def __init__(self, transform, size, tag, assets, layer=0, isScroll=True, animation="idle"):
        super().__init__(transform, size, tag, assets, layer, isScroll, animation)
        self.speed = 400
        self.damage = 15

    def check_finished(self):
        for entity in self.entityCollisions:
            if entity.tag == "asteroid":
                self.asteroid.asteroid_particles(self.transform, self.particles)

    def hit_entity(self, sprite):
        pass

class SpreadProjectile(Projectile):
    def __init__(self, transform, size, tag, assets, layer=0, isScroll=True, animation="idle"):
        super().__init__(transform, size, tag, assets, layer, isScroll, animation)
        self.set_rotation(0)
        self.damage = 5
        self.maxAlive = 0.3
        self.currentAlive = 0
        self.hasSpawned = False

    def hit_entity(self, sprite):
        if self.canDoDamage:
            self.movement.y = 0
            self.hit = True
            self.canDoDamage = False

    def check_finished(self):
        if self.hit:
            self.kill()
        if self.asteroid:
            self.asteroid.asteroid_particles(self.transform, self.particles)

    def update_timers(self, dt):
        if self.hasSpawned and self.currentAlive > 0:
            self.currentAlive -= dt
        elif self.hasSpawned and self.currentAlive <= 0:
            self.kill()

    def update(self, dt, game, particles):
        super().update(dt, game, particles)
        self.update_timers(dt)

    def start(self, transform):
        super().start(transform)
        self.currentAlive = self.maxAlive
        self.hasSpawned = True

class SpreadWeapon(Weapon):
    def __init__(self, maxMagazine, reloadTime, isAutomatic, shootTime, bullet, muzzleAreas):
        super().__init__(maxMagazine, reloadTime, isAutomatic, shootTime, bullet, muzzleAreas)
        self.numBullets = 8
        self.spread = 40

    def shoot(self, game, transform):
        if self.canShoot and self.magazine > 0:
            muzzleTransforms = self.calculate_muzzle_areas(transform)
            for muzzle in muzzleTransforms:
                for i in range(self.numBullets):
                    # Calculate random spread angle
                    angle = random.uniform(-self.spread / 2, self.spread / 2)
                    
                    # Create bullet at muzzle transform
                    bullet = self.bullet.copy()
                    bullet.start(muzzle)
                    
                    # Adjust bullet direction based on spread angle
                    bullet_direction = pygame.math.Vector2(0, -1).rotate(angle)
                    bullet.movement = bullet_direction
                    
                    # Add to world and camera
                    game.projectiles.add(bullet)
                    game.add_to_world(bullet)

            # Start timer
            self.currentShootTime = self.shootTime
            self.magazine -= 1

    

    
