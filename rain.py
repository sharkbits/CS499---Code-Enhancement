"""Simulate terminal particles for weather effects such as rain and snow.

This module defines particle motion and a small engine that updates and draws
weather particles onto the app's frame buffer.
"""

import random

# from time import sleep
from dataclasses import InitVar, dataclass
from typing import ClassVar

# Weather tuning reference:
# Weather Type | drops_count | speed increment | GLOBAL_TTL
# Mist         | 10          | 0.02            | 0.5
# Light Rain   | 15          | 0.1             | 2.0
# Heavy Rain   | 40          | 0.4             | 5.0
# Snow         | 20          | 0.01            | 0.2


# ---------------- PARTICLE MODEL ----------------


@dataclass
class Particle:
    x: float
    y: float
    GLOBAL_TTL: InitVar[float]
    personal_TTL: float = 0.0
    speed: float = 0.0

    def __post_init__(self, GLOBAL_TTL):
        # Offset terminal velocity so particles do not move in lockstep.
        offset = random.uniform(-1.0, 1.0)
        self.personal_TTL = GLOBAL_TTL + offset

    def update(self):
        # Increment speed until it hits terminal velocity (TTL)
        if self.speed < self.personal_TTL:
            self.speed += 0.01

        self.y += self.speed


# ---------------- PARTICLE ENGINE ----------------


@dataclass
class ParticleEngine:
    terminal_width: int
    terminal_height: int
    # Shared pool allows the renderer to use one active particle set.
    _particle_pool: ClassVar[list[Particle]] = []
    particle_character: str = "*"
    global_ttl: float = 0.2
    particle_count: int = 20

    def __post_init__(self):
        if len(self.particle_character) != 1:
            raise ValueError("Particle character can be no longer than 1")
        # Prevent invalid dimensions before update/draw operations begin.
        if self.terminal_width == 0 and self.terminal_height == 0:
            raise ValueError("terminal width and terminal height cannot be 0")
        self._particle_pool.clear()

    def generate_particles(self):
        ParticleEngine._particle_pool = [
            Particle(
                random.uniform(0, self.terminal_width - 1),
                random.randint(0, self.terminal_height - 1),
                self.global_ttl,
            )
            for p in range(self.particle_count)
        ]

    def configure(
        self, particle_character: str, global_ttl: float, particle_count: int
    ):
        self.particle_character = particle_character
        self.global_ttl = global_ttl
        self.particle_count = particle_count
        self._particle_pool.clear()
        if particle_count > 0:
            self.generate_particles()

    def update_particles(self, canvas: list[list]):
        for particle in ParticleEngine._particle_pool:
            particle.update()
            # Reset drop to top if it goes off screen
            if particle.y >= self.terminal_height:
                particle.y = 0
                particle.x = random.randint(0, self.terminal_width - 1)
                self.speed = random.uniform(0.1, 0.5)

            ix, iy = int(particle.x), int(particle.y)
            if 0 <= iy < self.terminal_height and 0 <= ix < self.terminal_width:
                canvas[iy][ix] = self.particle_character


"""
# Configuration
width = 40
height = 15
drops_count = 20
pool = []


def generate_rain():
    for p in range(drops_count):
        start_x = random.randint(0, width - 1)
        start_y = random.randint(0, height - 1)
        pool.append(rain_drop(x=float(start_x), y=float(start_y)))


generate_rain()

    

# Test Loop
try:
    while True:
        # Clear the terminal (base on OS)
        os.system("cls" if os.name == "nt" else "clear")

        # Update all drops positions
        for p in pool:
            p.update(height, width)

        # Draw the frame
        frame = []
        for h in range(height):
            line = ""
            for w in range(width):
                # Check if any drop is at this current pixel
                if any(p.is_at(w, h) for p in pool):
                    line += "*"
                else:
                    line += " "
            frame.append(line)

        print("\n".join(frame))

        # 4. Control the frame rate
        sleep(0.05)

except KeyboardInterrupt:
    print("\nRain stopped.")

"""
