import math
import random

import pygame

import pgz
from pgz import keyboard

pgz.set_resource_root("demo/resources")


class Ship(pgz.Actor):
    def __init__(self):
        super().__init__(random.choice(["ship (1)", "ship (2)", "ship (3)", "ship (4)", "ship (5)", "ship (6)"]))

        self.speed = 200
        self.velocity = [0, 0]
        self._old_pos = self.pos

    def update(self, dt):
        self._old_pos = self.pos[:]

        # pressed = pygame.key.get_pressed()
        if keyboard.up:
            self.velocity[1] = -self.speed
        elif keyboard.down:
            self.velocity[1] = self.speed
        else:
            self.velocity[1] = 0

        if keyboard.left:
            self.velocity[0] = -self.speed
        elif keyboard.right:
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


class Game(pgz.MapScene):
    def __init__(self, map):
        super().__init__(map)

    def on_enter(self, previous_scene):
        super().on_enter(previous_scene)

        self.ship = Ship()
        self.add_actor(self.ship, central_actor=True)

        # put the ship in the center of the map
        self.ship.pos = self.map.get_center()

    def draw(self, screen: pgz.Screen):
        super().draw(screen)
        # self.screen.draw.text(text=self.client_data["name"], pos=(700, 0))
        self.screen.draw.text(text=f"from server {int(self.ship.x)}", pos=(500, 0))
        self.draw_health((1000, 10), 15)

    def draw_health(self, pos, value):
        w = 100
        h = 20
        pad = 3
        GREY = (100, 100, 100)
        RED = (255, 0, 0)
        color = RED

        # if value > 100:
        #     player_shield_color = pygame.GREEN
        #     player_shield = 100
        # elif value > 75:
        #     player_shield_color = pygame.GREEN
        # elif value > 50:
        #     player_shield_color = pygame.YELLOW
        # else:
        #     player_shield_color = pygame.RED

        self.screen.draw.rect(pgz.ZRect(pos[0] - pad, pos[1] - pad, w + 2 * pad, h + 2 * pad), GREY)
        self.screen.draw.filled_rect(pgz.ZRect(pos[0], pos[1], w * value / 100.0, h), color)

    def update(self, dt):
        """Tasks that occur over time should be handled here"""
        super().update(dt)

        if self.collide_map(self.ship):
            self.ship.move_back(dt)

        if self.collide_group(self.ship, "cannon_balls"):
            # pgz.sounds.arrr.play()
            print("BAM!")

    def on_mouse_move(self, pos):
        angle = self.ship.angle_to(pos) + 90
        self.ship.angle = angle

    def on_mouse_down(self, pos, button):
        # pgz.sounds.arrr.play()
        ball = CannonBall(self.ship.pos, pos)
        self.add_actor(ball, group_name="cannon_balls")


class Menu(pgz.MenuScene):
    def __init__(self):
        super().__init__()
        import pygame_menu

        self.menu = pygame_menu.Menu(300, 400, "Welcome", theme=pygame_menu.themes.THEME_BLUE)

        self.menu.add_text_input("Name :", default="John Doe")
        # self.menu.add_selector('Difficulty :', [('Hard', 1), ('Easy', 2)], onchange=set_difficulty)
        self.menu.add_button("Play", self.start_the_game)
        self.menu.add_button("Quit", pygame_menu.events.EXIT)

    def start_the_game(self):
        tmx = pgz.maps.default
        map = pgz.ScrollMap(app.resolution, tmx, ["Islands"])
        self.application.change_scene(Game(map))


if __name__ == "__main__":

    app = pgz.Application(
        title="pgz Standalone Demo",
        resolution=(1280, 720),
        update_rate=60,
    )

    try:
        menu = Menu()
        app.run(menu)

    except Exception:
        # pygame.quit()
        raise
