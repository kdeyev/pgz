import math
import random
from typing import Optional, Tuple

import pygame

import pgz

pgz.set_resource_root("demo/resources")

BLACK = tuple(pygame.Color("BLACK"))
RED = tuple(pygame.Color("RED"))
YELLOW = tuple(pygame.Color("YELLOW"))
GREEN = tuple(pygame.Color("GREEN"))


class Ship(pgz.Actor):
    def __init__(self) -> None:
        self.image_num = random.randrange(1, 6)
        super().__init__(f"ship ({self.image_num}) (1)")

        self.speed = 200
        self.health = 100.0
        self.velocity = [0, 0]
        self._old_pos = self.pos
        self._old_health = self.health

    def is_dead(self) -> bool:
        return self.health <= 0

    def update_sprite(self):
        num = 1
        if self.health <= 0:
            num = 4
        elif self.health <= 33:
            num = 3
        elif self.health <= 66:
            num = 2

        ang = self.angle
        self.image = f"ship ({self.image_num}) ({num})"
        self.angle = ang
        self._old_health = self.health

    def update(self, dt):
        if self.health != self._old_health:
            self.update_sprite()

        if self.is_dead():
            return

        self._old_pos = self.pos[:]

        # pressed = pygame.key.get_pressed()
        if self.keyboard.up:
            self.velocity[1] = -self.speed
        elif self.keyboard.down:
            self.velocity[1] = self.speed
        else:
            self.velocity[1] = 0

        if self.keyboard.left:
            self.velocity[0] = -self.speed
        elif self.keyboard.right:
            self.velocity[0] = self.speed
        else:
            self.velocity[0] = 0

        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt
        # self.rect.topleft = self._position

    def move_back(self, dt):
        """If called after an update, the sprite can move back"""
        self.pos = self._old_pos[:]
        # self.rect.topleft = self._position


class CannonBall(pgz.Actor):
    def __init__(self, pos, target):
        super().__init__("cannonball")

        self.pos = pos
        self.target = target
        self.speed = 400.0

        self.hit_rate = 10.0  # HP/second

        self.reached = False
        self.explosion_phases = 3

    def decrement_explosion_phases(self):
        if self.explosion_phases == 0:
            self.deleter(self)
        else:
            self.image = f"explosion{self.explosion_phases}"
            self.explosion_phases -= 1
            pgz.global_clock.schedule(self.decrement_explosion_phases, 0.1)

    def update(self, dt):
        if self.reached:
            return

        if self.distance_to(self.target) < 5:
            self.reached = True
            self.explosion_phases = 3
            self.decrement_explosion_phases()
        else:
            angle = self.angle_to(self.target)
            self.x += math.cos(math.radians(angle)) * self.speed * dt
            self.y -= math.sin(math.radians(angle)) * self.speed * dt
        # self.rect.topleft = self._position


class GameScene(pgz.MapScene):
    def __init__(self):
        super().__init__()

    def on_enter(self, previous_scene):
        super().on_enter(previous_scene)

        self.ship = Ship()
        self.add_actor(self.ship, central_actor=True)

        # put the ship in the center of the map
        self.ship.pos = self.map.get_center()

    def draw(self, screen: pgz.Screen):
        super().draw(screen)
        screen.draw.text(text=self.client_data["name"], pos=(700, 0))
        screen.draw.text(text=f"from server {int(self.ship.x)}", pos=(500, 0))
        self.draw_health_bar(screen, self.ship.health)

    def draw_health_bar(self, screen, health):
        width = 300
        height = 20
        padding = 3
        pos = (screen.width - (width + 4 * padding), 2 * padding)
        health_bar_color = self.get_health_bar_color(health)

        screen.draw.rect(pgz.ZRect(pos[0] - padding, pos[1] - padding, width + 2 * padding, height + 2 * padding), BLACK)
        screen.draw.filled_rect(pgz.ZRect(pos[0], pos[1], width * health / 100.0, height), health_bar_color)

    def get_health_bar_color(self, health):
        if health > 75:
            return GREEN
        elif health > 50:
            return YELLOW
        else:
            return RED

    def update(self, dt):
        """Tasks that occur over time should be handled here"""
        super().update(dt)

        if self.ship.is_dead():
            return

        if self.collide_map(self.ship):
            self.ship.move_back(dt)

        cannon_ball = self.collide_group(self.ship, "cannon_balls")

        if cannon_ball:
            # pgz.sounds.arrr.play()
            self.ship.health -= cannon_ball.hit_rate * dt

    def on_mouse_move(self, pos):
        if self.ship.is_dead():
            return

        angle = self.ship.angle_to(pos) + 90
        self.ship.angle = angle

    def on_mouse_down(self, pos, button):
        if self.ship.is_dead():
            return

        start_point = self.calc_cannon_ball_start_pos(pos)
        if start_point:
            ball = CannonBall(pos=start_point, target=pos)
            self.add_actor(ball, group_name="cannon_balls")

    def calc_cannon_ball_start_pos(self, pos) -> Optional[Tuple[float, float]]:
        distance = self.ship.distance_to(pos)
        min_distance = math.sqrt((self.ship.width / 2) ** 2 + (self.ship.height / 2) ** 2)
        if distance < min_distance:
            # too close to the ship
            return None
        angle = self.ship.angle_to(pos)
        start_point = (
            self.ship.pos[0] + min_distance * math.cos(math.radians(angle)),
            self.ship.pos[1] - min_distance * math.sin(math.radians(angle)),
        )
        return start_point
