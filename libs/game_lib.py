from libs import options_lib, physics_lib, particle_lib, camera_lib, widgets_lib
from collections import deque

import pygame
import math
import random
import json
import os


class Game:
    def __init__(self):
        self.undo_history = deque()
        self.redo_history = deque()

        self.screen_size: pygame.Vector2 = pygame.Vector2(*options_lib.screen_size)
        self.window = widgets_lib.Window(
            screen_size=self.screen_size
        )

        self.topleft_menu = widgets_lib.DynamicTextWidget(
            shift=pygame.Vector2(0, 0),
            text=[],
            font=options_lib.main_font,
            line_dif=pygame.Vector2(0, options_lib.main_font.get_height()),
            color=(0, 0, 0)
        )

        self.bottomright_menu = widgets_lib.DynamicTextWidget(
            shift=pygame.Vector2(0, 0),
            text=["", ""],
            font=options_lib.main_font,
            line_dif=pygame.Vector2(0, options_lib.main_font.get_height()),
            color=(0, 0, 0),
            alignment="bottomright",
            master_alignment="bottomright"
        )

        self.particle_select_menu = widgets_lib.ButtonWidget(
            shift=pygame.Vector2(-10, 10),
            size=pygame.Vector2(300, 500),
            color=(100, 100, 100, 100),
            alignment="topright",
            master_alignment="topright",
        )

        self.static_particle_properties = widgets_lib.DynamicTextWidget(
            shift=pygame.Vector2(0, 0),
            font=options_lib.main_font,
            line_dif=pygame.Vector2(0, options_lib.main_font.get_height()),
            color=(0, 0, 0),
            text=[
                "$name"
            ],
            alignment="midtop",
            master_alignment="midtop"
        )

        self.dynamic_particle_properties = widgets_lib.DynamicTextWidget(
            shift=pygame.Vector2(0, 50),
            font=options_lib.main_font,
            line_dif=pygame.Vector2(0, options_lib.main_font.get_height()),
            color=(0, 0, 0),
            text=[
                "$velocity",
                "$kinetic_energy"
            ],
            alignment="midtop",
            master_alignment="midtop"
        )

        self.particle_select_menu.set_children(
            self.static_particle_properties,
            self.dynamic_particle_properties,
            widgets_lib.ButtonWidget(
                widgets_lib.DynamicTextWidget(
                    shift=pygame.Vector2(0, 0),
                    text=("Remove particles",),
                    font=options_lib.main_font,
                    color=(0, 0, 0),
                    alignment="center",
                    master_alignment="center"
                ),
                shift=pygame.Vector2(0, 150),
                size=pygame.Vector2(260, 50),
                color=(200, 50, 50),
                alignment="midtop",
                master_alignment="midtop",
                button_down_event=self.button_event_remove_focused
            ),
            widgets_lib.ButtonWidget(
                widgets_lib.DynamicTextWidget(
                    shift=pygame.Vector2(0, 0),
                    text=("Freeze particles",),
                    font=options_lib.main_font,
                    color=(0, 0, 0),
                    alignment="center",
                    master_alignment="center"
                ),
                shift=pygame.Vector2(0, 220),
                size=pygame.Vector2(260, 50),
                color=(100, 150, 250),
                alignment="midtop",
                master_alignment="midtop",
                button_down_event=self.button_event_freeze_focused
            )
        )
        self.particle_select_menu.visible = False

        self.window.event_handler = self.event_handler

        self.window.add_children(self.topleft_menu, self.bottomright_menu, self.particle_select_menu)

        self.particle_radius_square = options_lib.particle_radius ** 2

        self.real_mouse_pos = pygame.Vector2(0, 0)
        self.screen_mouse_pos = pygame.Vector2(0, 0)

        self.screen_size = pygame.Vector2(*self.window.window_surface.get_size())
        self.screen_middle: pygame.Vector2 = self.screen_size / 2

        self.running = False
        self.simulating = True

        self.particles = []

        self.walls = True
        self.wall_radius = 500

        self.average_kinetic = 0
        self.average_potential = 0

        self.shown_particles = 0

        self.pressed = NO_PRESS
        self.focused_particles = set()

        self.selection_rect = pygame.Rect(0, 0, 0, 0)

        self.new_particle = particle_lib.Particle(1, 0, 0, 0, 0, 0, pygame.Vector2(0, 0))

        self.clock = pygame.time.Clock()

        self.camera = camera_lib.Camera(self, self.screen_size, self.screen_middle)

        self.update_scale()
        self.update_particle_picker()

        self.window.start()

    def physics(self):
        if self.simulating:
            for particle_no, particle in enumerate(self.particles):
                particle.vel += physics_lib.gravity * physics_lib.delta_time

                if self.walls:
                    if particle.pos.x >= self.wall_radius:
                        particle.vel += pygame.Vector2(
                            physics_lib.kw * physics_lib.delta_time * (-self.wall_radius + particle.pos.x), 0)

                    elif particle.pos.x <= - self.wall_radius:
                        particle.vel += pygame.Vector2(
                            physics_lib.kw * physics_lib.delta_time * (self.wall_radius + particle.pos.x), 0)

                    if particle.pos.y >= self.wall_radius:
                        particle.vel += pygame.Vector2(
                            0, physics_lib.kw * physics_lib.delta_time * (-self.wall_radius + particle.pos.y))

                    elif particle.pos.y <= - self.wall_radius:
                        particle.vel += pygame.Vector2(
                            0, physics_lib.kw * physics_lib.delta_time * (self.wall_radius + particle.pos.y))

                for other_particle in self.particles[:particle_no]:
                    delta = particle.pos - other_particle.pos
                    distance_sqr = delta.magnitude_squared()

                    if distance_sqr != 0:
                        distance = math.sqrt(distance_sqr)

                        force_vector = delta.normalize() * physics_lib.net_force(
                            particle.muon_coefficient(other_particle),
                            distance, distance_sqr)

                        particle.vel += force_vector * physics_lib.delta_time
                        other_particle.vel -= force_vector * physics_lib.delta_time

                particle.pos += particle.vel * physics_lib.delta_time

            kinetic, potential = self.calculate_energy()

            self.average_kinetic = (self.average_kinetic * (
                    AVERAGING_COEFFICIENT - 1) + kinetic) / AVERAGING_COEFFICIENT
            self.average_potential = (self.average_potential * (
                    AVERAGING_COEFFICIENT - 1) + potential) / AVERAGING_COEFFICIENT

    def draw(self):
        # Reset
        self.window.window_surface.blit(self.camera.background, (0, 0))

        # Shadow
        pygame.draw.circle(self.window.window_surface, options_lib.colors["shadow"], self.screen_mouse_pos.xy,
                           int(options_lib.particle_radius * self.camera.zoom_amount))

        # Particles
        shown_particles = 0

        for particle in self.particles:
            screen_pos = self.camera.real_to_screen_vector(particle.pos)
            if self.camera.is_visible_screen(screen_pos):
                shown_particles += 1

                if particle in self.focused_particles:
                    pygame.draw.circle(self.window.window_surface, options_lib.colors["focus"], screen_pos.xy,
                                       int(self.camera.real_to_screen_size(options_lib.particle_radius) * 2), 2)

                pygame.draw.circle(self.window.window_surface, particle.color, screen_pos,
                                   int(self.camera.real_to_screen_size(options_lib.particle_radius)))

                if self.topleft_menu.visible:
                    particle.rect.midbottom = self.camera.real_to_screen_vector(particle.pos + pygame.Vector2(0, -50))
                    self.window.window_surface.blit(particle.surface, particle.rect)

        # Meter
        for particle in self.focused_particles:
            screen_pos = self.camera.real_to_screen_vector(particle.pos)
            distance = (self.real_mouse_pos - particle.pos) / physics_lib.rn

            surface = options_lib.particles_font.render(f"{distance} ({int(distance.magnitude() * 100) / 100}) Rn",
                                                        True, options_lib.colors["meter"])
            rect = surface.get_rect()
            rect.midtop = pygame.Vector2(0, 50) + (screen_pos + self.screen_mouse_pos) / 2
            self.window.window_surface.blit(surface, rect)
            pygame.draw.line(self.window.window_surface, options_lib.colors["meter"], self.screen_mouse_pos, screen_pos)

        # Selection rect
        if self.pressed is PRESSED_CTRL:
            copied = self.selection_rect.copy()
            copied.normalize()
            pygame.draw.rect(self.window.window_surface, options_lib.colors["meter"],
                             self.camera.real_to_screen_rect(copied), 2)

        kinetic, potential = self.calculate_energy()

        # Topleft menu
        self.topleft_menu.set_texts(
            f"FPS: {int(self.clock.get_fps() * FPS_ROUND) / FPS_ROUND}",
            f"Particles: {len(self.particles)} ({shown_particles} shown)",
            f"",
            f"Kinetic: {kinetic:.2f}",
            f"Temperature: {0 if not len(self.particles) else kinetic / len(self.particles):.2f}",
            f"Potential: {potential:.2f}",
            f"Total: {(potential + kinetic):.2f}",
            f"Average Kinetic: {self.average_kinetic:.2f}",
            f"Average Temperature: {0 if not len(self.particles) else self.average_kinetic / len(self.particles):.2f}",
            f"Average Potential: {self.average_potential:.2f}",
            f"Pressed {self.pressed}"
        )
        self.topleft_menu.update_surface()

        self.window.update_surface()
        self.window.render()

    def calculate_energy(self):
        kinetic = 0
        potential = 0

        for particle_no, particle in enumerate(self.particles):
            kinetic += physics_lib.calculate_kinetic_energy_revion(particle)
            potential += physics_lib.calculate_potential_energy_revion(particle, particle_no, self.particles)

        return kinetic, potential

    def reset_averaged(self):
        self.average_kinetic, self.average_potential = self.calculate_energy()

    def toggle_simulation(self):
        self.simulating = not self.simulating

    def create_particle(self, particle):
        self.particles.append(particle)
        self.reset_averaged()

    # Button events
    def button_event_remove_focused(self, _):
        self.push_undo_history()

        for particle in self.particles:
            self.particles.remove(particle)

        self.focused_particles.clear()
        self.deselect_particles()

    def button_event_freeze_focused(self, _):
        self.push_undo_history()

        for particle in self.focused_particles:
            particle.vel = pygame.Vector2()

    def get_focused_pos(self):
        total = pygame.Vector2(0, 0)

        for particle in self.focused_particles:
            total += particle.pos

        return total / len(self.focused_particles)

    def get_focused_vel(self):
        total = pygame.Vector2(0, 0)

        for particle in self.focused_particles:
            total += particle.vel

        return total

    def get_focused_vel_mag(self):
        total = 0

        for particle in self.focused_particles:
            total += particle.vel.magnitude()

        return total

    def get_focused_avg_vel(self):
        total = pygame.Vector2(0, 0)

        for particle in self.focused_particles:
            total += particle.vel / len(self.focused_particles)

        return total

    def get_focused_avg_vel_mag(self):
        total = 0

        for particle in self.focused_particles:
            total += particle.vel.magnitude() / len(self.focused_particles)

        return total

    def get_focused_kinetic(self):
        return sum(physics_lib.calculate_kinetic_energy_revion(particle) for particle in self.focused_particles)

    def move_focused_particles(self, amount: pygame.Vector2):
        for particle in self.focused_particles:
            particle.pos += amount
            particle.vel = pygame.Vector2()

    def create_random_particle(self):
        self.create_particle(particle_lib.Particle(random.randint(-1, 1),
                                                   random.randint(-1, 1),
                                                   0,
                                                   random.randint(-1, 1),
                                                   0,
                                                   0,
                                                   pygame.Vector2(
                                                       random.randint(-int(self.wall_radius), int(self.wall_radius)),
                                                       random.randint(-int(self.wall_radius), int(self.wall_radius)))))

    def select_particle(self, particle):
        self.focused_particles.add(particle)

        self.update_static_select_menu()

    def select_particles(self, *particles):
        for particle in particles:
            self.focused_particles.add(particle)

        self.update_static_select_menu()

    def update_static_select_menu(self):
        if self.focused_particles:
            self.particle_select_menu.visible = True
            self.particle_select_menu.update_surface()

            if len(self.focused_particles) == 1:
                self.static_particle_properties.set_texts(
                    f"{tuple(self.focused_particles)[0]}"
                )

            else:
                self.static_particle_properties.set_texts(
                    f"{len(self.focused_particles)} selected"
                )

            self.static_particle_properties.update_surface()

        else:
            self.particle_select_menu.visible = False

    def switch_selection(self, particle):
        if particle in self.focused_particles:
            self.focused_particles.remove(particle)

        else:
            self.select_particle(particle)

        self.update_static_select_menu()

    def deselect_particles(self):
        self.focused_particles.clear()
        self.particle_select_menu.visible = False

    def deselect_particle(self, particle):
        self.focused_particles.remove(particle)

        self.update_static_select_menu()

    def clear_particles(self):
        self.particles.clear()
        self.focused_particles.clear()
        self.update_static_select_menu()

    def zoom(self, amount):
        self.camera.zoom(1.25 ** amount, self.zoom_position())
        self.update_scale()

    def update_particle_picker(self):
        self.bottomright_menu[0] = f"{self.new_particle}"
        self.bottomright_menu.update_surface()

    def update_scale(self):
        self.bottomright_menu[1] = f"x{self.camera.grid_zoom}"
        self.bottomright_menu.update_surface()

    def take_screenshot(self):
        file_no = 0

        while True:
            file_no += 1

            path = f"screenshots/screenshot_{str(file_no).rjust(4, '0')}.png"

            if os.path.isfile(path):
                continue

            pygame.image.save(self.window.window_surface, path)
            return

    def load_from_dict(self, data: dict):
        self.particles = []

        self.walls = data["walls"]["active"]
        self.wall_radius = data["walls"]["radius"]

        for particle in data["particles"]:
            self.particles.append(particle_lib.get_particle_from_dict(particle))

    def get_dict(self):
        return {
            "walls": {
                "active": self.walls,
                "radius": self.wall_radius
            },
            "particles": [particle.get_dict() for particle in self.particles]
        }

    def load_from_file(self, file_name):
        with open(file_name) as file:
            self.load_from_dict(json.load(file))

    def save_to_file(self, file_name):
        with open(file_name, "w") as file:
            json.dump(self.get_dict(), file)

    def quick_save(self):
        file_no = 0

        while True:
            file_no += 1

            path = f"saves/save_{str(file_no).rjust(4, '0')}.json"

            if os.path.isfile(path):
                continue

            self.save_to_file(path)
            return

    def loop(self):
        self.running = True

        while self.running:
            self.window.get_events()

            self.screen_mouse_pos.xy = pygame.mouse.get_pos()
            self.real_mouse_pos = self.camera.screen_to_real_vector(self.screen_mouse_pos)

            if self.particle_select_menu.visible:
                self.dynamic_particle_properties.set_texts(
                    f"sum(V)/n = {self.get_focused_avg_vel().magnitude():.2f} rn/s",
                    f"sum|V|/n = {self.get_focused_avg_vel_mag():.2f} rn/s",
                    f"E = {self.get_focused_kinetic():.2f} R"
                )
                self.dynamic_particle_properties.update_surface()
                self.particle_select_menu.update_surface()

            self.physics()
            self.draw()
            self.clock.tick()

    def event_handler(self, event):
        if event.type == pygame.QUIT:
            self.running = False

        elif event.type == pygame.MOUSEWHEEL:
            self.zoom(event.y)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.key.get_mods() & pygame.KMOD_CTRL and event.button == pygame.BUTTON_LEFT:
                self.pressed = PRESSED_CTRL
                self.selection_rect = pygame.Rect(self.real_mouse_pos, (0, 0))

            else:
                self.window.focused = None

                for particle in self.particles:
                    if (particle.pos - self.real_mouse_pos).magnitude_squared() <= \
                            self.particle_radius_square:

                        # Mouse is on a particle
                        if event.button == pygame.BUTTON_LEFT and particle in self.focused_particles:
                            self.pressed = PRESSED_PARTICLE

                        elif event.button == pygame.BUTTON_RIGHT:
                            if not pygame.key.get_mods() & pygame.KMOD_CTRL:
                                self.deselect_particles()

                            self.switch_selection(particle)

                        return

                # Mouse is not on a particle
                if event.button == pygame.BUTTON_LEFT:
                    if self.walls and (
                            abs(self.real_mouse_pos.x) >= self.wall_radius or
                            abs(self.real_mouse_pos.y) >= self.wall_radius
                    ):
                        self.pressed = PRESSED_WALL
                        self.push_undo_history()

                    else:
                        self.pressed = PRESSED_NONE

                    self.deselect_particles()

                elif event.button == pygame.BUTTON_RIGHT:
                    self.push_undo_history()
                    particle_ = self.new_particle.copy()
                    particle_.pos = self.real_mouse_pos.copy()
                    self.create_particle(particle_)

        elif event.type == pygame.MOUSEMOTION:
            if self.pressed is PRESSED_NONE:
                self.camera.move(event.rel)

            elif self.pressed is PRESSED_PARTICLE:
                self.move_focused_particles(pygame.Vector2(event.rel))

            elif self.pressed is PRESSED_WALL:
                self.wall_radius = max(abs(self.real_mouse_pos.x), abs(self.real_mouse_pos.y))
                self.camera.get_background()

            elif self.pressed is PRESSED_CTRL:
                self.selection_rect.size = self.real_mouse_pos - pygame.Vector2(self.selection_rect.topleft)

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.pressed is PRESSED_CTRL:
                self.selection_rect.normalize()

                if not pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.deselect_particles()

                self.select_particles(*(particle for particle in self.particles if
                                        self.selection_rect.collidepoint(particle.pos)))

            self.pressed = NO_PRESS

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.toggle_simulation()

            elif event.key == pygame.K_a:
                self.new_particle.a = (self.new_particle.a + 2) % 3 - 1
                self.update_particle_picker()

            elif event.key == pygame.K_b:
                self.new_particle.b = (self.new_particle.b + 2) % 3 - 1
                self.update_particle_picker()

            elif event.key == pygame.K_c:
                self.new_particle.c = (self.new_particle.c + 2) % 3 - 1
                self.update_particle_picker()

            elif event.key == pygame.K_x:
                self.new_particle.x = (self.new_particle.x + 2) % 3 - 1
                self.update_particle_picker()

            elif event.key == pygame.K_y:
                if event.mod % pygame.KMOD_CTRL:
                    self.pop_redo_history()
                    return

                self.new_particle.y = (self.new_particle.y + 2) % 3 - 1
                self.update_particle_picker()

            elif event.key == pygame.K_z:
                if event.mod % pygame.KMOD_CTRL:
                    self.pop_undo_history()
                    return

                self.new_particle.z = (self.new_particle.z + 2) % 3 - 1
                self.update_particle_picker()

            elif event.key == pygame.K_F2:
                self.take_screenshot()

            elif event.key == pygame.K_F3:
                self.quick_save()

            elif event.key == pygame.K_o:
                self.push_undo_history()
                self.clear_particles()

            elif event.key == pygame.K_r:
                self.push_undo_history()
                self.clear_particles()

                for i in range(int(4 * self.wall_radius * self.wall_radius / physics_lib.rn ** 2)):
                    self.create_random_particle()

            elif event.key == pygame.K_f:
                self.push_undo_history()

                for particle in self.particles:
                    particle.vel = pygame.Vector2(0, 0)

                self.reset_averaged()

            elif event.key == pygame.K_TAB:
                self.new_particle.reverse()
                self.update_particle_picker()

            elif event.key == pygame.K_s:
                self.simulating = True
                self.physics()
                self.simulating = False

            elif event.key == pygame.K_t:
                self.topleft_menu.visible = not self.topleft_menu.visible

            elif event.key == pygame.K_w:
                self.push_undo_history()
                self.walls = not self.walls
                self.camera.get_background()

            elif event.key == pygame.K_KP_PLUS:
                physics_lib.delta_time *= 1.5

            elif event.key == pygame.K_KP_MINUS:
                physics_lib.delta_time *= 2 / 3

            elif event.key == pygame.K_ESCAPE:
                self.running = False

    def push_undo_history(self):
        self.redo_history = deque()
        self.undo_history.append(([particle.copy() for particle in self.particles], self.walls, self.wall_radius))

    def pop_undo_history(self):
        if not len(self.undo_history):
            return

        self.redo_history.append(([particle.copy() for particle in self.particles], self.walls, self.wall_radius))
        self.particles, self.walls, self.wall_radius = self.undo_history.pop()
        self.deselect_particles()

    def pop_redo_history(self):
        if not len(self.redo_history):
            return

        self.undo_history.append(([particle.copy() for particle in self.particles], self.walls, self.wall_radius))
        self.particles, self.walls, self.wall_radius = self.redo_history.pop()
        self.deselect_particles()

    def zoom_position(self):
        return (
            None,
            pygame.Vector2(0, 0),
            self.screen_mouse_pos
        )[options_lib.options["zoom position keep behaviour"]]


# Visual constants
FPS_ROUND = 1e2
AVERAGING_COEFFICIENT = 1000

NO_PRESS = 0
PRESSED_NONE = 1
PRESSED_PARTICLE = 2
PRESSED_WALL = 3
PRESSED_CTRL = 4

PARTICLES_NONE = 0
PARTICLES_FOCUSED = 1
PARTICLES_ALL = 2

# Zoom position keep behaviours:
# 0: Keep middle
# 1: Keep topleft
# 2: Keep mouse
