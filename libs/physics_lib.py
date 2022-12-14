from libs import particle_lib

import pygame

km = 1e6
kt = 2e8
kw = -1e-1

rn = kt / km
cp = km / rn ** 2 / 6
cf = km / rn ** 3

symmetric_linear_trimer_stability_constant = 289 ** (1 / 3) - 8

gravity = pygame.Vector2(0, 0)

delta_time = 0.1


def pixel_to_ru(x):
    return x / rn


def ru_to_pixel(x):
    return x * rn


def rewton_to_gauss(x):
    return x / cf


def gauss_to_rewton(x):
    return x * cf


def tsei_to_revion(x):
    return x / cp


def revion_to_tsei(x):
    return x * cp


def is_stable(w):
    return w > 0


def perfect_distance_pixel(w):
    return rn / w


def perfect_distance_ru(w):
    return 1 / w


def limit_distance_pixel(w):
    return rn * 2 / 3 / w


def limit_distance_ru(w):
    return 2 * rn / 3 / w


def resting_potential(w):
    return - w * w * w


def is_symmetric_trimer_stable(symmetric_bonds, outer_bond):
    return outer_bond / symmetric_bonds > symmetric_linear_trimer_stability_constant


def get_linearity_constant(bond1, bond2):
    return bond1 * bond2 / (bond1 + bond2)


def calculate_kinetic_energy(particle):
    """
    Calculates kinetic energy in Revions.
    """
    return particle.vel.magnitude_sqr / 2


def calculate_kinetic_energy_revion(particle: particle_lib.Particle):
    """
    Calculates kinetic energy in Revions.
    """
    return particle.vel.magnitude_squared() / 2 / cp


def calculate_potential_energy_revion(particle, other_particle):
    """
    Calculates the potential energy in Revions.
    """

    delta = other_particle.pos - particle.pos
    x = delta.magnitude() / rn

    if x == 0:
        return float("nan")

    w = particle.muon_coefficient(other_particle)

    return (2 - 3 * x * w) / x / x / x


def net_force(w, distance, distance_sqr):
    """
    Calculates the net force in Rewton.
    """
    return km * (rn - w * distance) / distance_sqr / distance_sqr


def net_force_gauss(w, distance, distance_sqr):
    """
    Calculates the net force in Gauss.
    """
    return (1 - w * distance) / distance_sqr / distance_sqr


def phi(w1, w2):
    """
    Calculates the phi value (linearity constant) for trigonics.
    """
    return w1 * w2 / (w1 + w2)


def calculate_energy(*particles: particle_lib.Particle):
    """
    Calculates both kinetic and potential energy in Revions.
    """
    kinetic = 0
    potential = 0

    for particle_no, particle in enumerate(particles):
        kinetic += calculate_kinetic_energy_revion(particle)

        for other_particle in particles[:particle_no]:
            potential += calculate_potential_energy_revion(particle, other_particle)

    return kinetic, potential
