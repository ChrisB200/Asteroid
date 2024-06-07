# Modules
import pygame
import sys
import logging
from pygame.constants import *

# Scripts
from scripts.camera import Window
from scripts.settings import Settings
from scripts.entities import Player, ModifiedSpriteGroup, UFO, Background, Asteroid
from scripts.animation import load_animations
from scripts.input import Controller, Keyboard, controller_check
from scripts.constants import BASE_IMG_PATH
from scripts.projectile import *
from scripts.particles import Particle, ParticleSystem
from scripts.waves import WaveSystem
from scripts.menu import RectElement, UserInterface, AnimatedElement, TextElement, SurfaceElement, Group

# configure the logger
logging.basicConfig(
    level=logging.INFO,  # set the log level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
    handlers=[
        logging.FileHandler("game.log"),  # Log to a file
        logging.StreamHandler()          # Also log to console
    ]
)

logger = logging.getLogger(__name__)

class Game():
    def __init__(self):
        logging.basicConfig(filename="data/game.log", level=logging.INFO)
        pygame.init()
        pygame.mixer.init()
        pygame.font.init()
        pygame.joystick.init()

        # core properties
        self.settings = Settings()
        self.window = Window(self.settings.resolution, flags=pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED)
        self.clock = pygame.time.Clock()
        self.assets = load_animations(BASE_IMG_PATH)
        self.inputDevices = []
        self.dt = 1
        self.state = "running"

        # sprite groups
        self.players = ModifiedSpriteGroup()
        self.projectiles = ModifiedSpriteGroup()
        self.ufos = ModifiedSpriteGroup()
        self.asteroids = ModifiedSpriteGroup()
        self.arrows = ModifiedSpriteGroup()
        self.explosions = ModifiedSpriteGroup()
        self.other = ModifiedSpriteGroup()
        self.items = ModifiedSpriteGroup()

        # background
        self.bgImage = pygame.image.load("data/bg.png")
        self.background = Background((0, 0), self.bgImage, -10)
        self.bgScroll = 1

        self.asteroidsDestroyed = 0
        self.asteroidsMissed = 0
        self.totalAsteroidsStats = 0

        # waves
        self.waveSystem = WaveSystem(self)
        self.score = 0

        # weapons and projectiles
        self.DEFAULT_PROJECTILE = Projectile((0, 0), (13, 13), "lasarbeam", self.assets, layer=0)
        self.DEFAULT_WEAPON = Weapon(50, 1, True, 0.1, self.DEFAULT_PROJECTILE, [[3, -5], [-16, -5]])

        self.MISSILE = Missile((0, 0), (11, 31), "missile", self.assets)
        self.MISSILE_WEAPON = Weapon(5, 2, False, 0.7, self.MISSILE, [[7, 0]])

        self.PIERCING_PROJECTILE = PiercingProjectile((0, 0), (13, 13), "piercing", self.assets, layer=0)
        self.PIERCING_WEAPON = Weapon(75, 0.5, True, 0.1, self.PIERCING_PROJECTILE, [[3, -5], [-16, -5]])

        self.SPREADING_PROJECTILE = SpreadProjectile((0, 0), (13, 13), "spread", self.assets, layer=0)
        self.SPREADING_WEAPON = SpreadWeapon(25, 0.7, True, 0.05, self.SPREADING_PROJECTILE, [[-3, 0]])
        
        self.BEAM_WEAPON = BeamWeapon(1, 50, 1, True, 0.2, self.DEFAULT_PROJECTILE, [[7, 0]])
        self.particles = ParticleSystem((0, 0))

        # user interface elements
        self.ui = UserInterface(self.get_world_size())
        self.font = pygame.font.Font("data/fonts/retro-gaming.ttf", 12)

        self.heartElements = []
        self.healthTexts = []
        self.ammoTypeElements = []
        self.ammoTexts = []

        self.waveNumberText = TextElement((10, self.get_world_size()[1] - 20), "1", self.font)
        self.scoreText = TextElement((20, 20), "0", self.font)
        self.fpsText = TextElement((200, 200), "0", self.font)
        
        self.ui.add(*self.heartElements, *self.healthTexts, *self.ammoTypeElements, self.waveNumberText, *self.ammoTexts, self.scoreText)
        
        self.smallerFont = pygame.font.Font("data/fonts/retro-gaming.ttf", 10)
        self.deathBackground = RectElement((0, 0), (200, 200), (0, 0, 0, 150))

        self.totalAsteroids = TextElement((20, 30), "0", self.smallerFont)
        self.totalAsteroidsLabel = TextElement((20, 10), "Total Asteroids", self.smallerFont)

        self.asteroidStats = TextElement((20, 70), "0", self.smallerFont)
        self.asteroidsStatsLabel = TextElement((20, 50), "Destroyed Asteroids", self.smallerFont)
        
        self.missedAsteroids = TextElement((20, 110), "0", self.smallerFont)
        self.missedAsteroidsLabel = TextElement((20, 90), "Missed Asteroids", self.smallerFont)        

        self.scoreLabel = TextElement((20, 130), "Score", self.smallerFont)
        self.scoreStats = TextElement((20, 150), "0", self.smallerFont)
        
        self.retryButtonText = TextElement((80, 170), "Retry", self.smallerFont)  

        self.deathGroup = Group((100, 100), (200, 200))
        self.deathGroup.add(self.deathBackground, self.retryButtonText, self.asteroidsStatsLabel, self.missedAsteroids, self.missedAsteroidsLabel, self.asteroidStats, self.scoreLabel, self.scoreStats, self.totalAsteroids, self.totalAsteroidsLabel)
        
        self.deathGroup.center_element_x(self.asteroidsStatsLabel)
        self.deathGroup.set_visible(False)
        self.ui.add_group(self.deathGroup)
        
        self.dead = False
        self.window.ui = self.ui

    # adds sprites to world
    def add_to_world(self, *sprites):
        self.window.world.add(*sprites)

    # gets the scaled world size
    def get_world_size(self):
        return self.window.world.screenSize

    # detects input devices and appends them
    def detect_inputs(self):
        self.inputDevices = []
        self.inputDevices.append(Keyboard(self.settings.keyboard))

        try:
            joysticks = controller_check()
            for joystick in joysticks: 
                controller = Controller(self.settings.controller, joystick)
                self.inputDevices.append(controller)
                logger.info("Detected controller, name: %s, guid: %s", controller.name, controller.guid)
        except:
            logger.info("No controllers detected")

        logger.info("Detected %s input devices", len(self.inputDevices))

    # creates a player and assigns them input
    def create_player(self, pos, input=0, layer=0):
        numOfPlayers = len(self.players.sprites())
        player = Player(numOfPlayers, pos, (26, 17), "spaceship", self.assets, layer)

        input = self.inputDevices[input]
        weapons = [self.DEFAULT_WEAPON.copy(), self.MISSILE_WEAPON.copy(), self.PIERCING_WEAPON.copy(), self.SPREADING_WEAPON.copy()]

        player.input = input
        player.weapons = weapons
        player.weapon = player.weapons[0]

        self.create_player_interface()

        self.players.add(player)
        self.add_to_world(player)
    
    # creates the user interface for the player.
    def create_player_interface(self):
        numPlayers = len(self.players)
        size = self.get_world_size()
        match numPlayers:
            case 0:
                heart = AnimatedElement((20, 20), (11, 11), "heart", self.assets)
                healthText = TextElement((40, 20), "100", self.font)
                ammoText = TextElement((40, 40), f"{self.DEFAULT_WEAPON.magazine} / {self.DEFAULT_WEAPON.maxMagazine}", self.font)
                ammoType = AnimatedElement((17.5, 40), (15, 15), "lasarbeam", self.assets)
                ammoType.rotation = -90
            case 1:
                heart = AnimatedElement((size[0] - 90, 20), (11, 11), "heart", self.assets)
                healthText = TextElement((size[0] - 70, 20), "100", self.font)
                ammoText = TextElement((size[0] - 70, 40), f"{self.DEFAULT_WEAPON.magazine} / {self.DEFAULT_WEAPON.maxMagazine}", self.font)
                ammoType = AnimatedElement((size[0] - 92, 40), (15, 15), "lasarbeam", self.assets)
                ammoType.rotation = -90

        self.heartElements.append(heart)
        self.healthTexts.append(healthText)
        self.ammoTypeElements.append(ammoType)
        self.ammoTexts.append(ammoText)

        self.ui.add(heart, healthText, ammoText, ammoType)

    # updates the user interface for each player
    def update_player_interface(self):
        for count, player in enumerate(self.players):
            self.healthTexts[count].change_text(str(player.health))
            self.ammoTexts[count].change_text(f"{player.weapon.magazine} / {player.weapon.maxMagazine}")
            self.ammoTypeElements[count].change_tag(player.weapon.bullet.tag)
            self.ammoTypeElements[count].rotation = player.weapon.bullet.rotation
            if player.weapon.magazine == 0:
                self.ammoTexts[count].change_colour((180, 0, 0))
            else:
                self.ammoTexts[count].change_colour((255, 255, 255))

    # calculate the differnce between frames
    def calculate_deltatime(self):
        self.dt = self.clock.tick() / 1000

    # draws the window
    def draw(self):
        self.particles.draw(self.window.world)
        self.window.world.draw_scrolling_background(self.background, self.bgScroll)
        self.window.draw_world()
        self.window.draw_foreground()
        self.window.draw_ui()
        self.window.draw()
        pygame.display.flip()

    # background scrolling
    def scroll_background(self):
        self.bgScroll += self.dt * 75
        if self.bgScroll >= self.background.height:
            self.bgScroll = 0

    # game updates
    def update(self):
        self.window.update()
        self.scroll_background()

        self.totalAsteroids.change_text(str(self.totalAsteroidsStats))
        self.asteroidStats.change_text(str(self.asteroidsDestroyed))
        self.missedAsteroids.change_text(str(self.asteroidsMissed))
        self.scoreStats.change_text(str(self.score))

        player: Player
        for player in self.players:
            player.update([], self.dt, self.window.world, self)
            if player.health <= 0: self.state = "dead"

        for projectile in self.projectiles:
            projectile.update(self.dt, self, self.particles)

        for ufo in self.ufos:
            ufo.update(self.dt, self.window.world, self)

        for arrow in self.arrows:
            arrow.update(self.dt)

        for asteroid in self.asteroids:
            asteroid.update(self.dt, self)

        for item in self.items:
            item.update(self.dt)
            item.check_collisions(self.players)
            item.transform.y += self.dt * 30

        self.update_player_interface()
        self.deathGroup.dock(self.get_world_size(), True, False)

        self.scoreText.change_text(str(self.score))
        self.fpsText.change_text(str(self.clock.get_fps()))
        self.scoreText.center_text_x(self.window.world.screenSize)
        
        self.particles.update(self.dt, (0, 0))
        
        if self.state == "running":
            self.waveSystem.update(self.waveNumberText)
        if self.state == "dead":
            for sprite in self.asteroids:
                sprite.kill()
            for sprite in self.ufos:
                sprite.kill()
        self.ui.update(self.dt, self.window.world)

    # handles the event
    def event_handler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state = ""
            if event.type == self.ASTEROID_SPAWN:
                self.totalAsteroidsStats += 1
            if event.type == self.ASTEROID_MISSED:
                self.asteroidsMissed += 1
            if event.type == self.ASTEROID_DESTROYED:
                self.asteroidsDestroyed += 1

            for player in self.players:
                player.event_handler(event, self)

            if event.type == pygame.MOUSEBUTTONDOWN:
                print("MouseDown")
                if event.button == 1 and self.state == "dead":
                    print("pressed")
                    if self.retryButtonText in self.ui.hoveredElements:
                        print("dead")
                        self.start_game()

            self.waveSystem.event_handler(event)

    def death_screen(self):
        if not self.dead:
            self.ui.add_group(self.deathGroup)
            self.dead = True

        pygame.mouse.set_visible(True)
        self.deathGroup.set_visible(True)
        self.retryButtonText.set_active(True)

    def start_game(self):
        self.players.empty()
        self.projectiles.empty()
        self.ufos.empty()
        self.asteroids.empty()
        self.arrows.empty()
        self.explosions.empty()
        self.other.empty()
        self.items.empty()
        self.ui.elements = []
        self.window.world.empty()

        self.waveSystem = WaveSystem(self)
        self.score = 0
        self.state = "running"

        self.deathGroup.set_visible(False)
        self.deathGroup.set_active(False)

        self.ASTEROID_SPAWN = USEREVENT + 4
        self.ASTEROID_MISSED = USEREVENT + 5
        self.ASTEROID_DESTROYED = USEREVENT + 6

        # user interface elements

        self.heartElements = []
        self.healthTexts = []
        self.ammoTypeElements = []
        self.ammoTexts = []

        self.asteroidsDestroyed = 0
        self.asteroidsMissed = 0
        self.totalAsteroidsStats = 0

        self.waveNumberText = TextElement((10, self.get_world_size()[1] - 20), "1", self.font)
        self.scoreText = TextElement((20, 20), "0", self.font)
        self.fpsText = TextElement((200, 200), "0", self.font)
        
        self.ui.add(*self.heartElements, *self.healthTexts, *self.ammoTypeElements, self.waveNumberText, *self.ammoTexts, self.scoreText)
        
        self.smallerFont = pygame.font.Font("data/fonts/retro-gaming.ttf", 10)
        self.deathBackground = RectElement((0, 0), (200, 200), (0, 0, 0, 150))

        self.totalAsteroids = TextElement((20, 30), "0", self.smallerFont)
        self.totalAsteroidsLabel = TextElement((20, 10), "Total Asteroids", self.smallerFont)

        self.asteroidStats = TextElement((20, 70), "0", self.smallerFont)
        self.asteroidsStatsLabel = TextElement((20, 50), "Destroyed Asteroids", self.smallerFont)
        
        self.missedAsteroids = TextElement((20, 110), "0", self.smallerFont)
        self.missedAsteroidsLabel = TextElement((20, 90), "Missed Asteroids", self.smallerFont)        

        self.scoreLabel = TextElement((20, 130), "Score", self.smallerFont)
        self.scoreStats = TextElement((20, 150), "0", self.smallerFont)
        
        self.retryButtonText = TextElement((80, 170), "Retry", self.smallerFont)  

        self.deathGroup = Group((100, 100), (200, 200))
        self.deathGroup.add(self.deathBackground, self.retryButtonText, self.asteroidsStatsLabel, self.missedAsteroids, self.missedAsteroidsLabel, self.asteroidStats, self.scoreLabel, self.scoreStats, self.totalAsteroids, self.totalAsteroidsLabel)
        
        self.deathGroup.center_element_x(self.asteroidsStatsLabel)
        self.deathGroup.set_visible(False)
        self.dead = False

        self.create_player((200, 20), 0, layer=2)

    # runs the game
    def run(self):
        self.detect_inputs()
        self.start_game()
        #self.create_player((300, 20), 0, layer=2)
        
        while True:
            if self.state == "running":
                pygame.mouse.set_visible(False)
                self.calculate_deltatime()
                self.event_handler()
                self.update()
                self.draw()
                #print(int(self.clock.get_fps()))
            if self.state == "dead":
                self.update()
                self.calculate_deltatime()
                self.death_screen()
                self.draw()
                self.event_handler()
            if self.state == "":
                break
            
if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()
