import math
import random
from typing import Optional, Tuple

import pygame
import pygame_menu

import pgz

pgz.set_resource_root("demo/resources")

BLACK = tuple(pygame.Color("BLACK"))
RED = tuple(pygame.Color("RED"))
YELLOW = tuple(pygame.Color("YELLOW"))
GREEN = tuple(pygame.Color("GREEN"))


class Ship(pgz.MultiplayerActor):
    def __init__(self) -> None:
        super().__init__(random.choice(["ship (1)", "ship (2)", "ship (3)", "ship (4)", "ship (5)", "ship (6)"]))

        self.speed = 200
        self.health = 100.0
        self.velocity = [0, 0]
        self._old_pos = self.pos

    def update(self, dt):
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


class CannonBall(pgz.MultiplayerActor):
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
        # self.screen.draw.text(text=self.client_data["name"], pos=(700, 0))
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

        if self.collide_map(self.ship):
            self.ship.move_back(dt)

        cannon_ball = self.collide_group(self.ship, "cannon_balls")

        if cannon_ball:
            # pgz.sounds.arrr.play()
            self.ship.health -= cannon_ball.hit_rate * dt

    def on_mouse_move(self, pos):
        angle = self.ship.angle_to(pos) + 90
        self.ship.angle = angle

    def on_mouse_down(self, pos, button):
        # pgz.sounds.arrr.play()
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


class ServerScene(pgz.Scene):
    def __init__(self, port):
        super().__init__()
        self.port = port

    def on_enter(self, previous_scene):
        super().on_enter(previous_scene=previous_scene)

        tmx = pgz.maps.default
        map = pgz.ScrollMap((1280, 720), tmx, ["Islands"])

        # Build and start game server
        self.server = pgz.MultiplayerSceneServer(map, GameScene)
        self.server.start_server(port=self.port)

    def on_exit(self, next_scene: Optional[pgz.Scene]):
        self.server.stop_server()
        self.server = None

    def update(self, dt):
        super().update(dt)
        if self.server:
            self.server.update(dt)


class Menu(pgz.MenuScene):
    def __init__(
        self,
    ):
        super().__init__()

        self.server = None

        self.menu = pygame_menu.Menu(300, 400, "Server", theme=pygame_menu.themes.THEME_BLUE)
        self.build_menu()

    def start_the_game(self):
        data = self.menu.get_input_data()
        port = data["port"]

        game = ServerScene(port)
        self.change_scene(game)

    def build_menu(self):
        self.menu.clear()
        if not self.server:
            self.port_widget = self.menu.add_text_input("Port :", textinput_id="port", default="8765", valid_chars=[str(i) for i in range(9)])
            self.menu.add_button("Start", self.start_the_game)
        else:
            self.menu.add_button("Stop", self.stop_the_game)

        self.menu.add_button("Quit", pygame_menu.events.EXIT)


if __name__ == "__main__":
    app = pgz.Application(
        title="pgz Server Demo",
        resolution=(1280, 720),
        update_rate=60,
    )

    try:

        menu = Menu()
        app.run(menu)

    except Exception:
        # pygame.quit()
        raise
