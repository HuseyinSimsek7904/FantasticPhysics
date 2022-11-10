from libs import vector_lib, options_lib, physics_lib


class Particle:
    def __init__(self, a, b, c, x, y, z, pos: vector_lib.Vector, vel: vector_lib.Vector = None):
        self.a = a
        self.b = b
        self.c = c

        self.x = x
        self.y = y
        self.z = z

        self.color = self.get_color()

        self.pos = pos

        if vel is None:
            self.vel = vector_lib.Vector(0, 0)

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

    def update(self, vel_change):
        self.vel.add(vel_change, physics_lib.delta_time)

        self.vel.x = self.vel.x
        self.vel.y = self.vel.y

        self.pos.add(self.vel, physics_lib.delta_time)

    def copy(self):
        return Particle(self.a, self.b, self.c, self.x, self.y, self.z, self.pos.copy(), self.vel.copy())
