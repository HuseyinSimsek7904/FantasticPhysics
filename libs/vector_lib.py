import pygame
import math


class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def set_tuple(self, tuple_):
        self.x, self.y = tuple_

    def set(self, vector_):
        self.x, self.y = vector_.x, vector_.y

    @property
    def tuple(self):
        return self.x, self.y

    @property
    def int_tuple(self):
        return int(self.x), int(self.y)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __neg__(self):
        return Vector(-self.x, -self.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vector(self.x * other, self.y * other)

    def __truediv__(self, other):
        return Vector(self.x / other, self.y / other)

    def __floordiv__(self, other):
        return Vector(int(self.x / other), int(self.y / other))

    @property
    def magnitude_sqr(self):
        return self.x * self.x + self.y * self.y

    @property
    def magnitude(self):
        return math.sqrt(self.magnitude_sqr)

    @property
    def normalized(self):
        return self / self.magnitude

    def add(self, vector, times=1.0):
        self.x += vector.x * times
        self.y += vector.y * times

    def add_(self, x, y, times=1.0):
        self.x += x * times
        self.y += y * times

    def draw(self, surface, start, color):
        pygame.draw.line(surface, color, start.screen_pos, (start + self).screen_pos, 2)

    def is_zero(self):
        return not self.x and not self.y

    def __repr__(self):
        return f"({int(self.x * 100) / 100}, {int(self.y * 100) / 100})"

    def copy(self):
        return Vector(self.x, self.y)
