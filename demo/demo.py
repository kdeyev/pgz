import pygame

import pgz

pgz.set_resource_root("demo/resources")


class Ship(pgz.Actor):
    def __init__(self):
        super().__init__("ship")

        self.speed = 200
        self.velocity = [0, 0]
        self._old_pos = self.pos

    def update(self, dt):
        from pgz import keyboard

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
    def __init__(self, pos, target, deleter):
        super().__init__("cannonball")

        self.deleter = deleter
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


class QuestGame(pgz.Scene):
    def __init__(self, map):
        self.map = map

        self.ship = Ship()
        # put the ship in the center of the map
        self.ship.position = self.map.get_center()
        self.ship.x += 600
        self.ship.y += 400

        # add our ship to the group
        self.map.add_sprite(self.ship)

    def draw(self, surface):

        # center the map/screen on our Ship
        self.map.set_center(self.ship.pos)

        self.map.draw(surface)

    def update(self, dt):
        """Tasks that occur over time should be handled here"""
        self.map.update(dt)

        # check if the sprite's feet are colliding with wall
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail
        if self.map.collide(self.ship):
            self.ship.move_back(dt)

    def on_mouse_move(self, pos):
        pos = self.map.transform(pos)
        angle = self.ship.angle_to(pos) + 90
        self.ship.angle = angle

    def boom(self):
        print("boom")

    def on_mouse_down(self, pos, button):
        pos = self.map.transform(pos)

        pgz.sounds.arrr.play()

        ball = CannonBall(self.ship.pos, pos, self.map.remove_sprite)
        self.map.add_sprite(ball)

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


if __name__ == "__main__":

    app = pgz.Application(
        title="My First EzPyGame Application!",
        resolution=(1280, 720),
        update_rate=60,
    )

    try:
        map = pgz.ScrollMap(app.resolution, "default.tmx", ["Islands"])
        game = QuestGame(map)
        app.run(game)

    except Exception:
        # pygame.quit()
        raise
