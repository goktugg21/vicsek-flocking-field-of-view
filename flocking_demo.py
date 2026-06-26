import math
import random
from vi import Agent, Config, Simulation, Window
from pygame.math import Vector2
import pygame

N = 150
fov = 360.0
noise = 0.6
speed = 2.0
radius = 50
world = 750

last_key = 0


def handle_keys():
    global noise, fov, last_key
    now = pygame.time.get_ticks()
    if now - last_key < 130:
        return
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        noise = min(5.0, round(noise + 0.2, 1))
    elif keys[pygame.K_DOWN]:
        noise = max(0.0, round(noise - 0.2, 1))
    elif keys[pygame.K_RIGHT]:
        fov = min(360.0, fov + 30.0)
    elif keys[pygame.K_LEFT]:
        fov = max(30.0, fov - 30.0)
    else:
        return
    last_key = now
    print("noise =", noise, "  fov =", fov)


class Bird(Agent):
    def on_spawn(self):
        angle = random.uniform(-math.pi, math.pi)
        self.move = Vector2(math.cos(angle), math.sin(angle)) * speed

    def update(self):
        handle_keys()

        heading = math.atan2(self.move.y, self.move.x)
        cos_half = math.cos(math.radians(fov) / 2)

        sum_x = math.cos(heading)
        sum_y = math.sin(heading)
        for other, _ in self.in_proximity_accuracy():
            d = other.pos - self.pos
            if d.length() == 0:
                continue
            if math.cos(heading) * d.x + math.sin(heading) * d.y >= cos_half * d.length():
                other_heading = math.atan2(other.move.y, other.move.x)
                sum_x += math.cos(other_heading)
                sum_y += math.sin(other_heading)

        average = math.atan2(sum_y, sum_x)
        new_angle = average + noise * (random.random() - 0.5)
        self.move = Vector2(math.cos(new_angle), math.sin(new_angle)) * speed

    def change_position(self):
        self.there_is_no_escape()
        self.pos += self.move


Simulation(
    Config(
        radius=radius,
        window=Window(width=world, height=world),
        movement_speed=speed,
        image_rotation=True,
        fps_limit=60,
        duration=0,
    )
).batch_spawn_agents(N, Bird, images=["images/triangle.png"]).run()
