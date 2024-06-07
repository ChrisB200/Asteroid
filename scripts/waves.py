# Modules
import pygame
import logging
import random
from pygame.constants import *

# Scripts
from scripts.entities import Asteroid, UFO, ModifiedSpriteGroup

logger = logging.getLogger(__name__)

SPAWN_ASTEROID = USEREVENT + 1
SPAWN_UFO = USEREVENT + 2

# a specific wave
class Wave:
    def __init__(self, number, numAsteroids, numUFOs):
        self.number = number
        self.numAsteroids = numAsteroids
        self.numUfos = numUFOs
        self.asteroids = ModifiedSpriteGroup()
        self.ufos = ModifiedSpriteGroup()
        self.started = False
        self.running = False
        self.end = False

    def start_wave(self, game):
        self.numAsteroids = random.randint(self.numAsteroids, self.numAsteroids+5)
        self.numUfos = random.randint(self.numUfos, self.numUfos+5)

        for i in range(self.numAsteroids):
            asteroid = Asteroid((0, 0), (40, 38), "asteroid", game.assets)
            self.asteroids.add(asteroid)
            

        for i in range(self.numUfos):
            ufo = UFO((0, 0), (24, 19), "ufo", game.assets)
            self.ufos.add(ufo)

        self.started = True
        
        pygame.time.set_timer(SPAWN_ASTEROID, random.randrange(500, 2000))
        pygame.time.set_timer(SPAWN_UFO, random.randrange(500, 2000))

    def spawn_asteroid(self, game):
        stop = False
        for asteroid in self.asteroids:
            if not asteroid.spawned and not stop:
                asteroid.spawn(game.get_world_size(), game.window.world)
                game.asteroids.add(asteroid)
                game.add_to_world(asteroid)
                pygame.time.set_timer(SPAWN_ASTEROID, random.randrange(500, 2000))
                stop = True

    def spawn_ufo(self, game):
        stop = False
        for ufo in self.ufos:
            if not ufo.spawned and not stop:
                ufo.spawn(game.get_world_size())
                game.ufos.add(ufo)
                game.arrows.add(ufo.arrow)
                game.add_to_world(ufo, ufo.arrow)
                pygame.time.set_timer(SPAWN_UFO, random.randrange(500 - (self.number * 2), 2000 - (self.number * 2)))
                stop = True

    def event_handler(self, event, game):
        if game.state == "running":
            if event.type == SPAWN_ASTEROID:
                self.spawn_asteroid(game)
                pygame.event.post(pygame.event.Event(game.ASTEROID_SPAWN))
            if event.type == SPAWN_UFO:
                self.spawn_ufo(game)

    def update(self):
        asteroidsLeft = False
        ufosLeft = False

        for asteroid in self.asteroids:
            if not asteroid.spawned:
                asteroidsLeft = True

        for ufo in self.ufos:
            if not ufo.spawned:
                ufosLeft = True

        if not asteroidsLeft and not ufosLeft: 
            self.end = True

class WaveSystem:
    def __init__(self, game):
        self.waveNumber = 0
        self.wave = Wave(self.waveNumber, 20, 8)
        self.game = game

    def calculate_max_enemies(self):
        wave_calculation = int(0.5 * (self.waveNumber + 4)**2 + 0.5 * (self.waveNumber + 4))
        return random.randint(wave_calculation, wave_calculation + 2)

    def update(self, waveNumberText):
        self.wave.update()
        if self.wave.end:
            self.waveNumber += 1
            waveNumberText.change_text(str(self.waveNumber))
            self.wave = Wave(self.waveNumber, self.calculate_max_enemies(), self.calculate_max_enemies())
            self.wave.start_wave(self.game)

    def event_handler(self, event):
        self.wave.event_handler(event, self.game)
