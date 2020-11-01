import math
import random
import time

import pygame
import pygame_menu

import pgz
from pgz.clock import FPSCalc

pgz.set_resource_root("demo/resources")


class Ship(pgz.MultiplayerActor):
    def __init__(self, uuid, deleter):
        super().__init__(random.choice(["ship (1)", "ship (2)", "ship (3)", "ship (4)", "ship (5)", "ship (6)"]), uuid, deleter)

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
    def __init__(self, uuid, deleter, pos, target):
        super().__init__("cannonball", uuid, deleter)

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
        self.fps_calc = FPSCalc()
        self.actor_factory = {"Ship": Ship, "CannonBall": CannonBall}

    def on_enter(self, previous_scene):
        # super().on_enter(previous_scene)

        self.ship = self.create_actor("Ship", central_actor=True)
        self.ship.x = 600
        # put the ship in the center of the map
        # self.ship.position = self.map.get_center()
        # self.ship.x += 600
        # self.ship.y += 400

    # def draw(self, surface):

    #     # center the map/screen on our Ship
    #     self.map.set_center(self.ship.pos)

    #     self.map.draw(surface)

    def update(self, dt):
        """Tasks that occur over time should be handled here"""
        # self.map.update(dt)
        super().update(dt)

        if self.map.collide(self.ship):
            self.ship.move_back(dt)

        self.fps_calc.push(1.0 / dt)
        if self.fps_calc.counter == 100:
            print(f"Scene {self.uuid} fps {self.fps_calc.aver()}")

    def on_mouse_move(self, pos):
        angle = self.ship.angle_to(pos) + 90
        self.ship.angle = angle

    def boom(self):
        print("boom")

    def on_mouse_down(self, pos, button):

        # pgz.sounds.arrr.play()

        ball = self.create_actor("CannonBall", pos=self.ship.pos, target=pos)

        # pgz.global_clock.schedule_interval(self.boom, 1)

    def on_key_down(self, key):
        if key == pygame.K_EQUALS:
            self.map.change_zoom(0.25)
        elif key == pygame.K_MINUS:
            self.map.change_zoom(-0.25)

    def handle_event(self, event):
        """Handle pygame input events"""

        # this will be handled if the window is resized
        if event.type == pygame.VIDEORESIZE:
            self.map.set_size((event.w, event.h))


class DummyScene(pgz.Scene):
    def __init__(self, menu=None):
        super().__init__()

    def draw(self, surface):
        pass
        # self.menu.mainloop(surface, disable_loop=True)

    def on_enter(self, previous_scene):
        super().on_enter(previous_scene=previous_scene)
        map = pgz.ScrollMap((1280, 720), "default.tmx", ["Islands"])
        # Supposed to have it's onw map
        self.server = pgz.MultiplayerSceneServer(map, GameScene)
        self.server.start_server()
        pass
        # self.menu.disable()

    def handle_event(self, event):
        pass
        # self.menu.update([event])

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

        game = DummyScene()
        self.application.change_scene(game)

    # def stop_the_game(self):
    #     self.server.stop_server()
    #     self.server = None

    #     self.build_menu()

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
