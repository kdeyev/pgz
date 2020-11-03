import math
import random
import time

import pygame
import pygame_menu

import pgz
from pgz.clock import FPSCalc
from pgz.rect import ZRect

pgz.set_resource_root("demo/resources")


class Ship(pgz.MultiplayerActor):
    def __init__(self):
        super().__init__(random.choice(["ship (1)", "ship (2)", "ship (3)", "ship (4)", "ship (5)", "ship (6)"]))

        self.speed = 200
        self.velocity = [0, 0]
        self._old_pos = self.pos
        self.dist_calc = FPSCalc()
        self.time_calc = FPSCalc()
        self.real_time_calc = FPSCalc()
        self.time = time.time()

    def update(self, dt):
        # from pgz import keyboard

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

        dx = self.velocity[0] * dt
        dy = self.velocity[1] * dt
        dist = math.sqrt(dx ** 2 + dy ** 2)

        self.dist_calc.push(dist)
        self.time_calc.push(dt)

        current_time = time.time()
        real_dt = current_time - self.time
        self.time = current_time
        self.real_time_calc.push(real_dt)

        if self.dist_calc.counter == 100:
            aver_dist = self.dist_calc.aver()
            aver_dt = self.time_calc.aver()
            aver_real_dt = self.real_time_calc.aver()
            print(f"Ship {self.uuid} average dist {aver_dist} average dt {aver_dt} aver_real_dt {aver_real_dt} aver speed {aver_dist/aver_dt}")

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

        self.reached = False
        self.explosion_phases = 3

    def decrement_explosion_phases(self):
        if self.explosion_phases == 0:
            self.deleter(self)
        else:
            self.image_name = f"explosion{self.explosion_phases}"
            self.explosion_phases -= 1
            pgz.global_clock.schedule(self.decrement_explosion_phases, 0.1)

    def update(self, dt):
        import math

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


class GameScene(pgz.MultiplayerClientHeadlessScene):
    def __init__(self):
        super().__init__()

    def on_enter(self, previous_scene):
        # super().on_enter(previous_scene)

        self.ship = Ship()
        self.ship = self.add_actor(self.ship, central_actor=True)

        # put the ship in the center of the map
        self.ship.pos = self.map.get_center()

    def draw(self, screen):
        self.client_data
        self.screen.draw.text(text=self.client_data["name"], pos=(700, 0))
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

        self.screen.draw.rect(ZRect(pos[0] - pad, pos[1] - pad, w + 2 * pad, h + 2 * pad), GREY, 3)
        self.screen.draw.filled_rect(ZRect(pos[0], pos[1], w * value / 100.0, h), color)

    def update(self, dt):
        """Tasks that occur over time should be handled here"""
        # self.map.update(dt)
        super().update(dt)

        if self.map.collide(self.ship):
            self.ship.move_back(dt)

    def on_mouse_move(self, pos):
        angle = self.ship.angle_to(pos) + 90
        self.ship.angle = angle

    def on_mouse_down(self, pos, button):
        # pgz.sounds.arrr.play()
        ball = CannonBall(pos=self.ship.pos, target=pos)
        self.add_actor(ball)


class ServerScene(pgz.Scene):
    def __init__(self, port):
        super().__init__()
        self.port = port

    def on_enter(self, previous_scene):
        super().on_enter(previous_scene=previous_scene)
        map = pgz.ScrollMap((1280, 720), "default.tmx", ["Islands"])

        # Build and start game server
        self.server = pgz.MultiplayerSceneServer(map, GameScene)
        self.server.start_server(port=self.port)

    def on_exit(self, next_scene):
        self.server.stop_server()
        self.server = None

    def update(self, dt):
        super().update(dt)
        if self.server:
            self.server.update(dt)

    # def draw(self, screen):
    #     super().draw(screen)
    #     self.screen.draw.text(self.server_url, pos=(300, 0))


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
        self.application.change_scene(game)

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
        title="My First EzPyGame Application!",
        resolution=(1280, 720),
        update_rate=60,
    )

    try:

        menu = Menu()
        app.run(menu)

    except Exception:
        # pygame.quit()
        raise
