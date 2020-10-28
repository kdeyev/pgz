import pygame

import pgz

HERO_MOVE_SPEED = 200


class Hero(pgz.Actor):
    def __init__(self):
        super().__init__("ship")

        self.velocity = [0, 0]
        self._old_pos = self.pos

    def update(self, dt):
        from pgz import keyboard

        self._old_pos = self.pos[:]

        # pressed = pygame.key.get_pressed()
        if keyboard.up:
            self.velocity[1] = -HERO_MOVE_SPEED
        elif keyboard.down:
            self.velocity[1] = HERO_MOVE_SPEED
        else:
            self.velocity[1] = 0

        if keyboard.left:
            self.velocity[0] = -HERO_MOVE_SPEED
        elif keyboard.right:
            self.velocity[0] = HERO_MOVE_SPEED
        else:
            self.velocity[0] = 0

        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt
        # self.rect.topleft = self._position

    def move_back(self, dt):
        """If called after an update, the sprite can move back"""
        self.pos = self._old_pos[:]
        # self.rect.topleft = self._position


class QuestGame(pgz.Scene):
    def __init__(self, map):
        self.map = map

        self.hero = Hero()
        # put the hero in the center of the map
        self.hero.position = self.map.get_center()
        self.hero.x += 600
        self.hero.y += 400

        # add our hero to the group
        self.map.add_sprite(self.hero)

    def draw(self, surface):

        # center the map/screen on our Hero
        self.map.set_center(self.hero.pos)

        self.map.draw(surface)

    def update(self, dt):
        """Tasks that occur over time should be handled here"""
        self.map.update(dt)

        # check if the sprite's feet are colliding with wall
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail
        if self.map.collide(self.hero):
            self.hero.move_back(dt)

    def on_mouse_move(self, pos):
        pos = self.map.transform(pos)
        angle = self.hero.angle_to(pos) + 90
        self.hero.angle = angle

    def boom(self):
        print("boom")

    def on_mouse_down(self, button):
        pgz.sounds.arrr.play()

        self.clock.schedule_interval(self.boom, 1)

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
        map = pgz.ScrollMap(app.resolution, "resources/maps/default.tmx", ["Islands"])
        game = QuestGame(map)
        app.run(game)

    except Exception:
        # pygame.quit()
        raise
