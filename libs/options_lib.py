import pygame
import json


def load_options():
    global options, colors, particle_radius, screen_size, fullscreen

    with open("options.json") as file:
        options = json.load(file)

    colors = {name: tuple(color) for name, color in options["colors"].items()}
    particle_radius = options["particle radius"]
    screen_size = tuple(options["screen size"])
    fullscreen = options["fullscreen"]


def update_font(camera_zoom):
    global particles_font
    particles_font = pygame.font.SysFont("Arial", int(options["particles font size"] * camera_zoom))


options = {}
colors = {}
particle_radius = 0
screen_size = 0, 0
fullscreen = False

load_options()

pygame.init()
particles_font = pygame.font.SysFont("Arial", int(options["particles font size"]))
