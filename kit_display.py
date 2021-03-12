
import pygame

class SharedDisplay(object):
    _instance = None
    
    def __new__(self, size=(480,480), fullscreen=False):
        fullscreen = pygame.FULLSCREEN if fullscreen else 0
        if not self._instance:
            self._instance = pygame.display.set_mode(size, fullscreen)  # pygame.FULLSCREEN
        return self._instance