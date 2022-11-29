from libs import options_lib

import pygame


class Particle:
    def __init__(self, a, b, c, x, y, z, pos: pygame.Vector2, vel: pygame.Vector2 = None):
        self.a = a
        self.b = b
        self.c = c

        self.x = x
        self.y = y
        self.z = z

        self.color = self.get_color()

        self.pos = pos

        if vel is None:
            self.vel = pygame.Vector2(0, 0)

        else:
            self.vel = vel

        self.surface = None
        self.rect = None
        self.get_text_surface()

    def get_text_surface(self):
        self.surface = options_lib.particles_font.render(repr(self), True, options_lib.colors["name"])
        self.rect = self.surface.get_rect()

    def anti(self):
        return Particle(-self.a, -self.b, -self.c, -self.x, -self.y, -self.z, self.pos)

    def muon_coefficient(self, other):
        return -self.a * other.a - self.b * other.b - self.c * other.c + (
                self.x * other.x + self.y * other.y + self.z * other.z)

    def reverse(self):
        self.a *= -1
        self.b *= -1
        self.c *= -1
        self.x *= -1
        self.y *= -1
        self.z *= -1

    def __repr__(self):
        if (not self.a) and (not self.b) and (not self.c) and (not self.x) and (not self.y) and (not self.z):
            return "0"

        return ("a" if self.a > 0 else ("a'" if self.a < 0 else "")) + \
               ("b" if self.b > 0 else ("b'" if self.b < 0 else "")) + \
               ("c" if self.c > 0 else ("c'" if self.c < 0 else "")) + \
               ("x" if self.x > 0 else ("x'" if self.x < 0 else "")) + \
               ("y" if self.y > 0 else ("y'" if self.y < 0 else "")) + \
               ("z" if self.z > 0 else ("z'" if self.z < 0 else ""))

    def get_color(self):
        return self.a * 50 + self.z * 50 + 100, self.b * 50 + self.y * 50 + 100, self.c * 50 + self.x * 50 + 100

    def copy(self):
        return Particle(self.a, self.b, self.c, self.x, self.y, self.z, self.pos.copy(), self.vel.copy())

    def get_dict(self, center_of_mass=pygame.Vector2(), reset_velocity=False):
        return {
            "pos": tuple(self.pos - center_of_mass),
            "vel": (0, 0) if reset_velocity else tuple(self.vel),
            "name": self.__repr__()
        }


def get_particle_from_dict(data: dict):
    return get_particle_from_name(data["name"], pygame.Vector2(data["pos"]), pygame.Vector2(data["vel"]))


def get_particle_from_name(name: str, position: pygame.Vector2 = pygame.Vector2(0, 0),
                           velocity: pygame.Vector2 = pygame.Vector2(0, 0)) -> Particle:
    particle = Particle(0, 0, 0, 0, 0, 0, position, velocity)

    last = ""
    for letter in name:
        if letter in "abcxyz":
            if last != "":
                if particle.__getattribute__(last) != 0:
                    raise ValueError("Invalid particle name.")

                particle.__setattr__(last, 1)

            last = letter

        elif letter == "'":
            if last == "" or particle.__getattribute__(last):
                raise ValueError("Invalid particle name.")

            particle.__setattr__(last, -1)
            last = ""

        else:
            raise ValueError("Invalid particle name.")

    if last:
        particle.__setattr__(last, 1)

    return particle
