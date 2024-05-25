import pygame

def circle_surf(radius, colour):
    surf = pygame.Surface((radius * 2, radius * 2))
    pygame.draw.circle(surf, colour, (radius, radius), radius)
    surf.set_colorkey((0, 0, 0))
    return surf