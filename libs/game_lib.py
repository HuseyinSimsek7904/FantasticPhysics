from libs import options_lib, physics_lib, particle_lib, camera_lib, widgets_lib
from collections import deque

import pygame
import math
import json
import os

pygame.init()


class Game:
    def __init__(self):
        self.undo_history = deque()
        self.redo_history = deque()

        self.screen_size: pygame.Vector2 = pygame.Vector2(options_lib.screen_size)

        if self.screen_size == pygame.Vector2():
            self.screen_size = pygame.Vector2(pygame.display.get_desktop_sizes()[0])

        self.screen_middle: pygame.Vector2 = self.screen_size / 2

        self.window = widgets_lib.Window(
            size=self.screen_size,
            children=(
                widgets_lib.DynamicTextWidget(
                    name="topleft-menu",
                    shift=pygame.Vector2(0, 0),
                    text=[
                        "$fps",
                        "$particles"
                    ],
                    font=widgets_lib.FontStyling(
                        size=20
                    )
                ),
                widgets_lib.DynamicTextWidget(
                    name="bottomright-menu",
                    shift=pygame.Vector2(0, 0),
                    text=[
                        "$name",
                        "$grid_size"
                    ],
                    alignment="bottomright",
                    parent_alignment="bottomright",
                    text_alignment="right",
                    font=widgets_lib.FontStyling(
                        size=20
                    )
                ),
                widgets_lib.ParentFrameWidget(
                    name="select-menu",
                    children=(
                        widgets_lib.DynamicTextWidget(
                            name="static-particle-properties",
                            shift=pygame.Vector2(0, 0),
                            text=(
                                "$name"
                            ),
                            alignment="midtop",
                            parent_alignment="midtop",
                            text_alignment="centerx",
                            font=widgets_lib.FontStyling(
                                size=20
                            )
                        ),
                        widgets_lib.DynamicTextWidget(
                            name="dynamic-particle-properties",
                            shift=pygame.Vector2(0, 50),
                            text=(
                                "$velocity",
                                "$kinetic_energy"
                            ),
                            alignment="midtop",
                            parent_alignment="midtop",
                            text_alignment="centerx",
                            font=widgets_lib.FontStyling(
                                size=20
                            )
                        ),
                        widgets_lib.ButtonWidget(
                            name="select-menu-remove",
                            children=(
                                widgets_lib.DynamicTextWidget(
                                    shift=pygame.Vector2(0, 0),
                                    text=("Remove particles",),
                                    alignment="center",
                                    parent_alignment="center",
                                    font=widgets_lib.FontStyling(
                                        size=20
                                    )
                                ),
                            ),
                            shift=pygame.Vector2(0, -20),
                            size=pygame.Vector2(260, 50),
                            background_color=(200, 50, 50),
                            alignment="midbottom",
                            parent_alignment="midbottom",
                            button_down_event=lambda _: self.remove_focused_particles()
                        ),
                        widgets_lib.ButtonWidget(
                            name="select-menu-freeze",
                            children=(
                                widgets_lib.DynamicTextWidget(
                                    shift=pygame.Vector2(0, 0),
                                    text=("Freeze particles",),
                                    alignment="center",
                                    parent_alignment="center",
                                    font=widgets_lib.FontStyling(
                                        size=20
                                    )
                                ),
                            ),
                            shift=pygame.Vector2(0, -80),
                            size=pygame.Vector2(260, 50),
                            background_color=(100, 150, 250),
                            alignment="midbottom",
                            parent_alignment="midbottom",
                            button_down_event=lambda _: self.freeze_focused_particles()
                        ),
                        widgets_lib.ButtonWidget(
                            name="select-menu-save",
                            children=(
                                widgets_lib.DynamicTextWidget(
                                    shift=pygame.Vector2(0, 0),
                                    text=("Save particles",),
                                    alignment="center",
                                    parent_alignment="center",
                                    font=widgets_lib.FontStyling(
                                        size=20
                                    )
                                ),
                            ),
                            shift=pygame.Vector2(0, -140),
                            size=pygame.Vector2(260, 50),
                            background_color=(20, 255, 50),
                            alignment="midbottom",
                            parent_alignment="midbottom",
                            button_down_event=lambda _: self.quick_save_focused()
                        )
                    ),
                    shift=pygame.Vector2(-10, 10),
                    size=pygame.Vector2(300, 500),
                    background_color=(100, 100, 100, 100),
                    alignment="topright",
                    parent_alignment="topright"
                )
            )
        )

        self.topleft_menu = self.window.find_name("topleft-menu")
        self.bottomright_menu = self.window.find_name("bottomright-menu")
        self.particle_select_menu = self.window.find_name("select-menu")
        self.dynamic_particle_properties = self.window.find_name("dynamic-particle-properties")

        self.particle_select_menu.hide()

        self.window.event_handler = self.event_handler

        self.real_mouse_pos = pygame.Vector2(0, 0)
        self.screen_mouse_pos = pygame.Vector2(0, 0)

        self.running = False
        self.simulating = True

        self.particles = []

        self.walls = True
        self.wall_radius = 500

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

                if self.walls and (self.pressed is not PRESSED_PARTICLE or particle not in self.focused_particles):
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

                        if self.pressed is not PRESSED_PARTICLE or particle not in self.focused_particles:
                            particle.vel += force_vector * physics_lib.delta_time

                        if self.pressed is not PRESSED_PARTICLE or other_particle not in self.focused_particles:
                            other_particle.vel -= force_vector * physics_lib.delta_time

                particle.pos += particle.vel * physics_lib.delta_time

    def draw(self):
        self.window.window.blit(self.camera.background, (0, 0))

        pygame.draw.circle(self.window.window, options_lib.colors["shadow"], self.screen_mouse_pos,
                           int(self.camera.real_to_screen_size(options_lib.particle_radius)))

        shown_particles = 0

        for particle in self.particles:
            screen_pos = self.camera.real_to_screen_vector(particle.pos)
            if self.camera.is_visible_screen(screen_pos):
                shown_particles += 1

                if particle in self.focused_particles:
                    pygame.draw.circle(self.window.window, options_lib.colors["focus"], screen_pos.xy,
                                       int(self.camera.real_to_screen_size(options_lib.particle_radius) * 2), 2)

                pygame.draw.circle(self.window.window, particle.color, screen_pos,
                                   int(self.camera.real_to_screen_size(options_lib.particle_radius)))

                if self.topleft_menu.visible:
                    particle.rect.midbottom = self.camera.real_to_screen_vector(particle.pos + pygame.Vector2(0, -50))
                    self.window.window.blit(particle.surface, particle.rect)

        for particle in self.focused_particles:
            screen_pos = self.camera.real_to_screen_vector(particle.pos)
            distance = (self.real_mouse_pos - particle.pos) / physics_lib.rn

            surface = options_lib.particles_font.render(
                f"{distance.x:.2f}, {distance.y:.2f} ({int(distance.magnitude() * 100) / 100}) ru",
                True, options_lib.colors["meter"])
            rect = surface.get_rect()
            rect.midtop = pygame.Vector2(0, 50) + (screen_pos + self.screen_mouse_pos) / 2
            self.window.window.blit(surface, rect)
            pygame.draw.line(self.window.window, options_lib.colors["meter"], self.screen_mouse_pos, screen_pos)

        if self.pressed is PRESSED_CTRL:
            copied = self.selection_rect.copy()
            copied.normalize()
            pygame.draw.rect(self.window.window, options_lib.colors["meter"],
                             self.camera.real_to_screen_rect(copied), 2)

        self.topleft_menu.set_texts(
            (
                f"FPS: {int(self.clock.get_fps() * FPS_ROUND) / FPS_ROUND}",
                f"Particles: {len(self.particles)} ({shown_particles} shown)"
            )
        )

        self.window.render()

    def toggle_simulation(self):
        self.simulating = not self.simulating

    def create_particle(self, particle):
        self.particles.append(particle)

    def freeze_focused_particles(self):
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

    def move_focused_particles(self, amount: pygame.Vector2):
        for particle in self.focused_particles:
            particle.pos += amount

    def remove_focused_particles(self):
        self.push_undo_history()

        for particle in self.focused_particles:
            self.particles.remove(particle)

        self.focused_particles.clear()
        self.deselect_all_particles()

    def select_particles(self, *particles: particle_lib.Particle):
        for particle in particles:
            self.focused_particles.add(particle)

        self.update_static_select_menu()

    def update_static_select_menu(self):
        static_select_menu = self.window.find_name("static-particle-properties")

        if self.focused_particles:
            self.particle_select_menu.show()

            if len(self.focused_particles) == 1:
                static_select_menu.set_texts(
                    (
                        f"{tuple(self.focused_particles)[0]}",
                    )
                )

            else:
                static_select_menu.set_texts(
                    (
                        f"{len(self.focused_particles)} selected",
                    )
                )

        else:
            self.particle_select_menu.hide()

    def switch_selections(self, *particles: particle_lib.Particle):
        for particle in particles:
            if particle in self.focused_particles:
                self.deselect_particle(particle)

            else:
                self.select_particles(particle)

        self.update_static_select_menu()

    def deselect_all_particles(self):
        self.focused_particles.clear()
        self.particle_select_menu.visible = False

    def deselect_particle(self, particle):
        self.focused_particles.remove(particle)

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

            pygame.image.save(self.window.window, path)
            return

    def load_from_dict(self, data: dict):
        if data["file-type"] != "simulation-data":
            raise ValueError("Invalid data for simulation data")

        self.particles = []

        self.walls = data["walls"]["active"]
        self.wall_radius = data["walls"]["radius"]

        for particle in data["particles"]:
            self.particles.append(particle_lib.get_particle_from_dict(particle))

    def get_dict(self):
        return {
            "file-type": "simulation-data",
            "walls": {
                "active": self.walls,
                "radius": self.wall_radius
            },
            **self.get_dict_of_focused()
        }

    def save_focused_to_file(self, file_name):
        with open(file_name, "w") as file:
            json.dump(self.get_dict_of_focused(True), file)

    def get_dict_of_focused(self, reset_velocity=False):
        center_of_mass = self.get_focused_pos()
        return {
            "file-type": "molecule-data",
            "particles": [particle.get_dict(center_of_mass, reset_velocity) for particle in self.focused_particles]
        }

    def load_from_file(self, file_name):
        with open(file_name) as file:
            self.load_from_dict(json.load(file))

    def quick_save_focused(self):
        file_no = 0

        while True:
            file_no += 1

            path = f"molecules/molecule_{str(file_no).rjust(4, '0')}.json"

            if os.path.isfile(path):
                continue

            self.save_focused_to_file(path)
            return

    def loop(self):
        self.running = True

        while self.running:
            self.window.get_events()

            self.screen_mouse_pos.xy = pygame.mouse.get_pos()
            self.real_mouse_pos = self.camera.screen_to_real_vector(self.screen_mouse_pos)

            if self.particle_select_menu.visible:
                kinetic, potential = physics_lib.calculate_energy(*self.focused_particles)

                self.dynamic_particle_properties.set_texts(
                    (
                        f"sum(V)/n = {self.get_focused_avg_vel().magnitude():.2f} ru/s",
                        f"sum||V||/n = {self.get_focused_avg_vel_mag():.2f} ru/s",
                        f"E = {kinetic:.2f} R",
                        f"H = {potential:.2f} R"
                    )
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
            self.window.focused = None
            if pygame.key.get_mods() & pygame.KMOD_CTRL and event.button == pygame.BUTTON_LEFT:
                self.pressed = PRESSED_CTRL
                self.selection_rect = pygame.Rect(self.real_mouse_pos, (0, 0))

            else:
                for particle in self.particles:
                    if (particle.pos - self.real_mouse_pos).magnitude_squared() <= \
                            options_lib.particle_radius * options_lib.particle_radius:

                        # Mouse is on a particle
                        if event.button == pygame.BUTTON_LEFT and particle in self.focused_particles:
                            self.pressed = PRESSED_PARTICLE
                            self.particle_select_menu.visible = False
                            self.freeze_focused_particles()

                        elif event.button == pygame.BUTTON_RIGHT:
                            if not pygame.key.get_mods() & pygame.KMOD_CTRL:
                                self.deselect_all_particles()

                            self.switch_selections(particle)

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

                    self.deselect_all_particles()

                elif event.button == pygame.BUTTON_RIGHT:
                    self.push_undo_history()
                    particle_ = self.new_particle.copy()
                    particle_.pos = self.real_mouse_pos.copy()
                    self.create_particle(particle_)

        elif event.type == pygame.MOUSEMOTION:
            if self.pressed is PRESSED_NONE:
                self.camera.move(event.rel)

            elif self.pressed is PRESSED_PARTICLE:
                self.move_focused_particles(self.camera.screen_to_real_size(pygame.Vector2(event.rel)))

            elif self.pressed is PRESSED_WALL:
                self.wall_radius = max(abs(self.real_mouse_pos.x), abs(self.real_mouse_pos.y))
                self.camera.get_background()

            elif self.pressed is PRESSED_CTRL:
                self.selection_rect.size = self.real_mouse_pos - pygame.Vector2(self.selection_rect.topleft)

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.pressed is PRESSED_CTRL:
                self.selection_rect.normalize()

                if not pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.deselect_all_particles()

                self.select_particles(*(particle for particle in self.particles if
                                        self.selection_rect.collidepoint(particle.pos)))

            if self.pressed is PRESSED_PARTICLE:
                self.particle_select_menu.visible = True

            self.pressed = NO_PRESS

        elif event.type == pygame.KEYDOWN:
            if event.mod & pygame.KMOD_CTRL:
                if event.key == pygame.K_a:
                    # CTRL + A
                    self.select_particles(*self.particles)

                elif event.key == pygame.K_f:
                    self.push_undo_history()

                    if self.focused_particles:
                        self.freeze_focused_particles()

                    else:
                        self.select_particles(*self.particles)
                        self.freeze_focused_particles()
                        self.deselect_all_particles()

                elif event.key == pygame.K_o:
                    self.push_undo_history()

                    if self.focused_particles:
                        self.remove_focused_particles()

                    else:
                        self.select_particles(*self.particles)
                        self.remove_focused_particles()

                elif event.key == pygame.K_d:
                    self.push_undo_history()

                    self.simulating = False

                    if self.focused_particles:
                        self.duplicate_focused_particles()

                    else:
                        self.select_particles(*self.particles)
                        self.duplicate_focused_particles()

            else:
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
                    self.select_particles(*self.particles)
                    self.quick_save_focused()
                    self.deselect_all_particles()

                elif event.key == pygame.K_TAB:
                    self.new_particle.reverse()
                    self.update_particle_picker()

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

    def duplicate_focused_particles(self):
        _, _, *size = self.focused_rect()
        size = pygame.Vector2(size) + pygame.Vector2(1, 1) * physics_lib.rn

        for particle in self.focused_particles:
            self.create_particle(particle.copy())

            particle.pos += size

    def focused_rect(self):
        if not self.focused_particles:
            return pygame.rect.Rect(0, 0, 0, 0)

        left = right = tuple(self.focused_particles)[0].pos.x
        top = bottom = tuple(self.focused_particles)[0].pos.y

        for particle in tuple(self.focused_particles)[1:]:
            left = min(left, particle.pos.x)
            top = min(top, particle.pos.y)
            right = max(right, particle.pos.x)
            bottom = max(bottom, particle.pos.y)

        return pygame.Rect(left, top, right - left, bottom - top)

    def push_undo_history(self):
        self.redo_history = deque()
        self.undo_history.append(([particle.copy() for particle in self.particles], self.walls, self.wall_radius))

    def pop_undo_history(self):
        if not len(self.undo_history):
            return

        self.redo_history.append(([particle.copy() for particle in self.particles], self.walls, self.wall_radius))
        self.particles, self.walls, self.wall_radius = self.undo_history.pop()
        self.deselect_all_particles()

    def pop_redo_history(self):
        if not len(self.redo_history):
            return

        self.undo_history.append(([particle.copy() for particle in self.particles], self.walls, self.wall_radius))
        self.particles, self.walls, self.wall_radius = self.redo_history.pop()
        self.deselect_all_particles()

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
