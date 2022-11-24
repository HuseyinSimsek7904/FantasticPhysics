from libs import options_lib
import pygame


class Window:
    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.window = pygame.display.set_mode(tuple(self.screen_size),
                                              flags=pygame.FULLSCREEN if options_lib.fullscreen else 0)

    def draw_circle_real(self, vector, color, radius):
        pass
