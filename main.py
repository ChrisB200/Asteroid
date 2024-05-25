# Modules
import pygame
import sys
import logging
from pygame.constants import *

# Scripts
from scripts.camera import Window
from scripts.settings import Settings
from scripts.entities import Player, ModifiedSpriteGroup, UFO
from scripts.animation import load_animations
from scripts.input import Controller, Keyboard, controller_check
from scripts.constants import BASE_IMG_PATH

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

        self.players = ModifiedSpriteGroup()
        self.bullets = ModifiedSpriteGroup()
        self.ufos = ModifiedSpriteGroup()
        self.asteroids = ModifiedSpriteGroup()
        self.arrows = ModifiedSpriteGroup()
        self.state = "running"

        self.bg = pygame.image.load("data/bg.png")

    def add_to_world(self, *sprites):
        self.window.world.add(*sprites)

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

    def create_player(self, pos, input=0, layer=0):
        numOfPlayers = len(self.players.sprites())
        player = Player(numOfPlayers, pos, (32, 32), "spaceship", self.assets, layer)

        input = self.inputDevices[input]
        player.input = input

        self.players.add(player)
        self.add_to_world(player)

    def calculate_deltatime(self):
        self.dt = self.clock.tick() / 1000

    # draws the window
    def draw(self):
        self.window.draw_world(image=self.bg)
        self.window.draw_foreground()
        self.window.draw()
        pygame.display.flip()

    def update(self):
        self.window.update()

        player: Player
        for player in self.players:
            player.update([], self.dt, self.window.world, self)
            print(player.health)
        
        for bullet in self.bullets:
            bullet.update(self.dt)

        for ufo in self.ufos:
            ufo.update(self.dt, self.window.world, self)

        for arrow in self.arrows:
            arrow.update(self.dt)

    def event_handler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state = ""
            if event.type == pygame.KEYDOWN:
                if event.key == K_SPACE:
                    ufo = UFO((0, 0), (32, 32), "ufo", self.assets)
                    ufo.spawn(self.window.world.screenSize)
                    self.ufos.add(ufo)
                    self.arrows.add(ufo.arrow)
                    self.add_to_world(ufo, ufo.arrow)
                    print(ufo.transform)

            for player in self.players:
                player.event_handler(event, self)

    def run(self):
        self.detect_inputs()
        self.create_player((200, 20), 0, layer=2)

        while self.state == "running":
            pygame.mouse.set_visible(False)
            self.calculate_deltatime()
            self.event_handler()
            self.update()
            self.draw()
            #print(int(self.clock.get_fps()))
            
if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()