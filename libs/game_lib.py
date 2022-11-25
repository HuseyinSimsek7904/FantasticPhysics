from libs import options_lib, physics_lib, particle_lib, camera_lib, window_lib
import pygame
import math
import random


class Game:
    def __init__(self):
        self.screen_size: pygame.Vector2 = pygame.Vector2(*options_lib.screen_size)
        self.window = window_lib.Window(self.screen_size)

        self.particle_radius_square = options_lib.particle_radius ** 2

        self.real_mouse_pos = pygame.Vector2(0, 0)
        self.screen_mouse_pos = pygame.Vector2(0, 0)

        self.screen_size = pygame.Vector2(*self.window.window.get_size())
        self.screen_middle: pygame.Vector2 = self.screen_size / 2

        self.simulating = True

        self.particles = []

        self.walls = True
        self.wall_radius = 500

        self.average_kinetic = 0
        self.average_potential = 0

        self.shown_particles = 0

        self.pressed_pos = None
        self.pressed_particle = None
        self.pressed_wall = False

        self.new_particle = particle_lib.Particle(1, 0, 0, 0, 0, 0, pygame.Vector2(0, 0))
        self.focused_particle = None

        self.show_statistics = True

        self.clock = pygame.time.Clock()

        self.camera = camera_lib.Camera(self, self.screen_size, self.screen_middle)

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

    def draw(self):
        # Reset
        self.window.window.blit(self.camera.background, (0, 0))

        # Shadow
        pygame.draw.circle(self.window.window, options_lib.colors["shadow"], self.screen_mouse_pos.xy,
                           int(options_lib.particle_radius * self.camera.zoom_amount))

        text_surface = options_lib.main_font.render(repr(self.new_particle), True,
                                                    options_lib.colors["meter"])
        text_rect = text_surface.get_rect()
        text_rect.topright = self.screen_size.x, 0
        self.window.window.blit(text_surface, text_rect)

        text_surface = options_lib.main_font.render(f"x{1 / self.camera.grid_zoom}", True,
                                                    options_lib.colors["meter"])
        text_rect = text_surface.get_rect()
        text_rect.topright = self.screen_size.x, 20
        self.window.window.blit(text_surface, text_rect)

        # Particles
        shown_particles = 0

        for particle in self.particles:
            screen_pos = self.camera.real_to_screen(particle.pos)
            if self.camera.is_visible_screen(screen_pos):
                shown_particles += 1
                if particle == self.focused_particle:
                    pygame.draw.circle(self.window.window, options_lib.colors["focus"], screen_pos.xy,
                                       int(options_lib.particle_radius * 2 * self.camera.zoom_amount), 2)

                pygame.draw.circle(self.window.window, particle.color, screen_pos.xy,
                                   int(options_lib.particle_radius * self.camera.zoom_amount))

                if self.show_statistics:
                    particle.rect.midbottom = self.camera.real_to_screen(particle.pos + pygame.Vector2(0, -50)).xy
                    self.window.window.blit(particle.surface, particle.rect)

        # Meter
        if self.focused_particle is not None:
            pygame.draw.line(self.window.window, options_lib.colors["meter"],
                             self.camera.real_to_screen(self.focused_particle.pos).xy, self.screen_mouse_pos.xy,
                             2)

            distance = (self.real_mouse_pos - self.focused_particle.pos) / physics_lib.rn

            surface = options_lib.particles_font.render(f"{distance} ({int(distance.magnitude() * 100) / 100}) Rn", True,
                                                        options_lib.colors["meter"])
            rect = surface.get_rect()
            rect.midtop = self.screen_mouse_pos.x, self.screen_mouse_pos.y + 50
            self.window.window.blit(surface, rect)

            coefficient = self.focused_particle.muon_coefficient(self.new_particle)
            if coefficient > 0:
                pygame.draw.circle(self.window.window, options_lib.colors["grid"], self.screen_middle.xy,
                                   int(physics_lib.rn / coefficient * self.camera.zoom_amount), 1)

        # FPS
        if self.show_statistics:
            surface = options_lib.main_font.render(f"FPS: {int(self.clock.get_fps() * FPS_ROUND) / FPS_ROUND}", True,
                                                   options_lib.colors["meter"])
            self.window.window.blit(surface, (0, 0))

            surface = options_lib.main_font.render(f"Particles: {len(self.particles)} ({shown_particles} shown)", True,
                                                   options_lib.colors["meter"])
            self.window.window.blit(surface, (0, 20))

            kinetic, potential = self.calculate_energy()

            if self.simulating:
                self.average_kinetic = (self.average_kinetic * (
                        AVERAGING_COEFFICIENT - 1) + kinetic) / AVERAGING_COEFFICIENT
                self.average_potential = (self.average_potential * (
                        AVERAGING_COEFFICIENT - 1) + potential) / AVERAGING_COEFFICIENT

            surface = options_lib.main_font.render(f"Kinetic: {int(kinetic * ENERGY_ROUND) / ENERGY_ROUND}", True,
                                                   options_lib.colors["meter"])
            self.window.window.blit(surface, (0, 70))

            surface = options_lib.main_font.render(
                f"Temperature: {0 if not len(self.particles) else int(kinetic / len(self.particles) * ENERGY_ROUND) / ENERGY_ROUND}",
                True, options_lib.colors["meter"])
            self.window.window.blit(surface, (0, 90))

            surface = options_lib.main_font.render(f"Potential: {int(potential * ENERGY_ROUND) / ENERGY_ROUND}", True,
                                                   options_lib.colors["meter"])
            self.window.window.blit(surface, (0, 110))

            surface = options_lib.main_font.render(f"Total: {int((potential + kinetic) * ENERGY_ROUND) / ENERGY_ROUND}",
                                                   True, options_lib.colors["meter"])
            self.window.window.blit(surface, (0, 130))

            surface = options_lib.main_font.render(
                f"Average Kinetic: {int(self.average_kinetic * ENERGY_ROUND) / ENERGY_ROUND}", True,
                options_lib.colors["meter"])
            self.window.window.blit(surface, (0, 150))

            surface = options_lib.main_font.render(
                f"Average Temperature: {0 if not len(self.particles) else int(self.average_kinetic / len(self.particles) * ENERGY_ROUND) / ENERGY_ROUND}",
                True, options_lib.colors["meter"])
            self.window.window.blit(surface, (0, 170))

            surface = options_lib.main_font.render(
                f"Average Potential: {int(self.average_potential * ENERGY_ROUND) / ENERGY_ROUND}", True,
                options_lib.colors["meter"])
            self.window.window.blit(surface, (0, 190))

        pygame.display.update()

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

    def remove_particle(self, particle):
        self.particles.remove(particle)

        if self.pressed_particle is particle:
            self.pressed_particle = None

        if self.focused_particle is particle:
            self.focused_particle = None

    def clear_particles(self):
        self.particles.clear()
        self.pressed_particle = None
        self.focused_particle = None
        self.reset_averaged()

    def frame(self):
        if self.pressed_particle is not None:
            self.pressed_particle.vel = pygame.Vector2(0, 0)

        if self.focused_particle is not None:
            self.camera.focus_on(self.focused_particle.pos)

        self.screen_mouse_pos.xy = pygame.mouse.get_pos()
        self.real_mouse_pos = self.camera.screen_to_real(self.screen_mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_WHEELUP:
                    self.camera.zoom(1.25)

                elif event.button == pygame.BUTTON_WHEELDOWN:
                    self.camera.zoom(0.8)

                else:
                    for particle in self.particles:
                        if (particle.pos - self.real_mouse_pos).magnitude_squared() <= \
                                self.particle_radius_square and particle is not self.focused_particle:
                            break

                    else:
                        # Mouse is not on a particle
                        if event.button == pygame.BUTTON_LEFT:
                            self.pressed_wall = False

                            if abs(self.real_mouse_pos.x) >= self.wall_radius and self.walls:
                                self.pressed_wall = True

                            elif abs(self.real_mouse_pos.y) >= self.wall_radius and self.walls:
                                self.pressed_wall = True

                            if self.focused_particle is not None:
                                self.focused_particle = None

                        elif event.button == pygame.BUTTON_RIGHT:
                            particle_ = self.new_particle.copy()
                            particle_.pos = self.real_mouse_pos.copy()
                            self.create_particle(particle_)

                        self.pressed_pos = self.real_mouse_pos

                        continue

                    # Mouse is on a particle
                    if event.button == pygame.BUTTON_LEFT:
                        self.pressed_particle = particle

                    elif event.button == pygame.BUTTON_RIGHT:
                        self.focused_particle = particle

            elif event.type == pygame.MOUSEMOTION:
                if self.pressed_particle is None:
                    if self.pressed_pos is not None:
                        if self.pressed_wall:
                            self.wall_radius = max(abs(self.real_mouse_pos.x), abs(self.real_mouse_pos.y))
                            self.camera.get_background()

                        else:
                            self.camera.move(event.rel)

                else:
                    self.pressed_particle.pos = self.real_mouse_pos.copy()

            elif event.type == pygame.MOUSEBUTTONUP:
                self.pressed_pos = None
                self.pressed_particle = None
                self.pressed_wall = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.toggle_simulation()

                elif event.key == pygame.K_a:
                    self.new_particle.a = (self.new_particle.a + 2) % 3 - 1

                elif event.key == pygame.K_b:
                    self.new_particle.b = (self.new_particle.b + 2) % 3 - 1

                elif event.key == pygame.K_c:
                    self.new_particle.c = (self.new_particle.c + 2) % 3 - 1

                elif event.key == pygame.K_x:
                    self.new_particle.x = (self.new_particle.x + 2) % 3 - 1

                elif event.key == pygame.K_y:
                    self.new_particle.y = (self.new_particle.y + 2) % 3 - 1

                elif event.key == pygame.K_z:
                    self.new_particle.z = (self.new_particle.z + 2) % 3 - 1

                elif event.key == pygame.K_F2:
                    self.take_screenshot()

                elif event.key == pygame.K_o:
                    self.clear_particles()

                elif event.key == pygame.K_d:
                    if self.focused_particle is not None:
                        self.remove_particle(self.focused_particle)

                elif event.key == pygame.K_r:
                    self.clear_particles()

                    for i in range(int(4 * self.wall_radius * self.wall_radius / physics_lib.rn ** 2)):
                        self.create_random_particle()

                elif event.key == pygame.K_f:
                    for particle in self.particles:
                        particle.vel = pygame.Vector2(0, 0)

                    self.reset_averaged()

                elif event.key == pygame.K_TAB:
                    self.new_particle.reverse()

                elif event.key == pygame.K_s:
                    self.simulating = True
                    self.physics()
                    self.simulating = False

                elif event.key == pygame.K_t:
                    self.show_statistics = not self.show_statistics

                elif event.key == pygame.K_w:
                    self.walls = not self.walls
                    self.camera.get_background()

                elif event.key == pygame.K_KP_PLUS:
                    physics_lib.delta_time *= 1.5

                elif event.key == pygame.K_KP_MINUS:
                    physics_lib.delta_time *= 2 / 3

                elif event.key == pygame.K_ESCAPE:
                    return True

        self.physics()
        self.draw()
        self.clock.tick(120)

        return False

    def take_screenshot(self):
        import os

        file_no = 0

        while True:
            file_no += 1

            path = f"screenshots/screenshot_{str(file_no).rjust(4, '0')}.png"

            if not os.path.isfile(path):
                pygame.image.save(self.window.window, path)
                break


# Visual constants
ENERGY_ROUND = 1e4
FPS_ROUND = 1e2
AVERAGING_COEFFICIENT = 1000
