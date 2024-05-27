# Modules
import pygame
import logging
from dataclasses import dataclass

# Scripts


logger = logging.getLogger(__name__)

TRIGGER_UP = pygame.USEREVENT + 1
TRIGGER_DOWN = pygame.USEREVENT + 2

@dataclass
class Controls:
    moveRight: int
    moveLeft: int
    moveDown: int
    moveUp: int
    dash: int
    pause: int
    shoot: int
    reload: int
    swapWeapon: int

class Trigger:
    def __init__(self, axis):
        self.axis = axis
        self.number = -1
        self.down = False
        self.up = False
        self.activated = False
        self.stop = 0

    def get_trigger(self, joystick):
        self.number = joystick.get_axis(self.axis)
        
        # Check if the trigger is pressed beyond the stop threshold
        if self.number > self.stop:
            if not self.activated:
                self.down = True
            else:
                self.down = False
            self.activated = True
            self.up = False
        elif self.number < self.stop:
            if self.activated:
                self.up = True
                self.activated = False
            else:
                self.up = False
            self.down = False
        else:
            self.down = False
            self.up = False

class Controller:
    def __init__(self, controls:Controls, joystick):
        # parameters
        self.controls = controls
        self.joystick = joystick
        self.guid = joystick.get_guid()
        self.name = joystick.get_name()
        
        # controller sticks
        self.leftStick = pygame.math.Vector2()
        self.rightStick = pygame.math.Vector2()
        self.leftTrigger = Trigger(4)
        self.rightTrigger = Trigger(5)

        # attributes
        self.deadzone = 0.1
        self.triggerStop = 0
        self.triggerActivated = False

    # reassigns the joystick to the controller
    def reassign_joystick(self, joystick):
        self.joystick = joystick
        self.guid = joystick.get_guid()
        self.name = joystick.get_name()

    # controls the deadzone - input below deadzone value is set to 0 to stop stick drift
    def control_deadzone(self, deadzone, *axes):
        newAxes = []
        for axis in axes:
            if abs(axis) < deadzone:
                axis = 0
            newAxes.append(axis)

        return newAxes

    # calculate sticks movement with deadzone
    def calculate_sticks(self):
        leftStick = self.control_deadzone(self.deadzone, self.joystick.get_axis(0), self.joystick.get_axis(1))
        rightStick = self.control_deadzone(self.deadzone, self.joystick.get_axis(2), self.joystick.get_axis(3))
        self.leftStick.x = leftStick[0]
        self.leftStick.y = leftStick[1]
        self.rightStick.x = rightStick[0]
        self.rightStick.y = rightStick[1]

    def calculate_triggers(self):
        self.leftTrigger.get_trigger(self.joystick)
        self.rightTrigger.get_trigger(self.joystick)

    # update the sticks
    def update(self):
        self.calculate_sticks()
        self.calculate_triggers()    
class Keyboard:
    def __init__(self, controls:Controls):
        self.controls = controls
        self.name = "keyboard"

    def update(self):
        pass

# Checks for controllers and initialises them
def controller_check():
    joysticks = []
    for i in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        joysticks.append(joystick)
    return joysticks
