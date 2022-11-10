from libs import vector_lib, options_lib, physics_lib
import pygame
import math


class Camera:
    def __init__(self, game, screen_size, screen_middle):
        self.game = game

        self.screen_size = screen_size
        self.screen_middle = screen_middle

        self.pos = vector_lib.Vector(0, 0)
        self.zoom_amount = 1

        self.grid_zoom = 1
        self.background = pygame.Surface(self.screen_size.tuple)
        self.get_background()

    def real_to_screen_x(self, number):
        return int((number - self.pos.x) * self.zoom_amount + self.screen_middle.x)

    def screen_to_real_x(self, number):
        return int((number - self.screen_middle.x) / self.zoom_amount + self.pos.x)

    def real_to_screen_y(self, number):
        return int((number - self.pos.y) * self.zoom_amount + self.screen_middle.y)

    def screen_to_real_y(self, number):
        return int((number - self.screen_middle.y) / self.zoom_amount + self.pos.y)

    def real_to_screen(self, vector: vector_lib.Vector):
        new = (vector - self.pos) * self.zoom_amount + self.screen_middle
        return vector_lib.Vector(int(new.x), int(new.y))

    def screen_to_real(self, vector: vector_lib.Vector):
        return (vector - self.screen_middle) / self.zoom_amount + self.pos

    def is_visible_screen(self, vector):
        return abs(vector.x - self.screen_middle.x) < self.screen_middle.x + \
               options_lib.particle_radius * self.zoom_amount and \
               abs(vector.y - self.screen_middle.y) < self.screen_middle.y + \
               options_lib.particle_radius * self.zoom_amount

    def is_visible_real(self, vector):
        return abs(vector.x - self.pos.x) * self.zoom_amount < self.screen_middle.x + \
               options_lib.particle_radius * self.zoom_amount and \
               abs(vector.y - self.pos.y) * self.zoom_amount < self.screen_middle.y + \
               options_lib.particle_radius * self.zoom_amount

    def zoom(self, amount):
        self.zoom_amount *= amount
        options_lib.update_font(self.zoom_amount)

        for particle in self.game.particles:
            particle.get_text_surface()

        self.get_background()

    def focus_on(self, vector: vector_lib.Vector):
        self.pos = vector.copy()
        self.get_background()

    def move(self, amount):
        self.pos.add_(*amount, -1 / self.zoom_amount)
        self.get_background()

    def get_background(self):
        self.background.fill(options_lib.colors["background"])

        self.grid_zoom = 10 ** math.ceil(math.log10(self.zoom_amount))

        # Grid
        for x in range(math.ceil(self.screen_to_real_x(0) / physics_lib.rn * self.grid_zoom),
                       math.ceil(self.screen_to_real_x(self.screen_size.x) / physics_lib.rn * self.grid_zoom)):
            color, width = options_lib.colors["origin"] if x == 0 else options_lib.colors["grid"], \
                           2 if x == 0 else 1
            x = self.real_to_screen_x(x / self.grid_zoom * physics_lib.rn)
            pygame.draw.line(self.background, color, (x, 0), (x, self.screen_size.y), width)

        for y in range(math.ceil(self.screen_to_real_y(0) / physics_lib.rn * self.grid_zoom),
                       math.ceil(self.screen_to_real_y(self.screen_size.y) / physics_lib.rn * self.grid_zoom)):
            color, width = options_lib.colors["origin"] if y == 0 else options_lib.colors["grid"], \
                           2 if y == 0 else 1
            y = self.real_to_screen_y(y / self.grid_zoom * physics_lib.rn)
            pygame.draw.line(self.background, color, (0, y), (self.screen_size.x, y), width)

        # Walls
        if self.game.walls:
            pygame.draw.rect(self.background, options_lib.colors["wall"],
                             (0, 0,
                              self.real_to_screen_x(-self.game.wall_radius), self.screen_size.y))

            pygame.draw.rect(self.background, options_lib.colors["wall"],
                             (self.real_to_screen_x(self.game.wall_radius), 0,
                              self.screen_size.x - self.real_to_screen_x(self.game.wall_radius), self.screen_size.y))

            pygame.draw.rect(self.background, options_lib.colors["wall"],
                             (0, 0,
                              self.screen_size.x, self.real_to_screen_y(-self.game.wall_radius)))

            pygame.draw.rect(self.background, options_lib.colors["wall"],
                             (0, self.real_to_screen_y(self.game.wall_radius),
                              self.screen_size.x, self.screen_size.y - self.real_to_screen_y(self.game.wall_radius)))
