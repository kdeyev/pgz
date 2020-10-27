import pygame
from pygame.locals import K_DOWN, K_EQUALS, K_LEFT, K_MINUS, K_RIGHT, K_UP, KEYDOWN, VIDEORESIZE

import pgz
from scroll_map import ScrollMap

HERO_MOVE_SPEED = 200


# make loading images a little easier
def load_image(filename):
    return pygame.image.load(filename)


class Hero(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = load_image("resources/images/ship.png").convert_alpha()
        self.velocity = [0, 0]
        self._position = [0, 0]
        self._old_position = self.position
        self.rect = self.image.get_rect()

    @property
    def position(self):
        return list(self._position)

    @position.setter
    def position(self, value):
        self._position = list(value)

    def update(self, dt):
        self._old_position = self._position[:]

        pressed = pygame.key.get_pressed()
        if pressed[K_UP]:
            self.velocity[1] = -HERO_MOVE_SPEED
        elif pressed[K_DOWN]:
            self.velocity[1] = HERO_MOVE_SPEED
        else:
            self.velocity[1] = 0

        if pressed[K_LEFT]:
            self.velocity[0] = -HERO_MOVE_SPEED
        elif pressed[K_RIGHT]:
            self.velocity[0] = HERO_MOVE_SPEED
        else:
            self.velocity[0] = 0

        self._position[0] += self.velocity[0] * dt
        self._position[1] += self.velocity[1] * dt
        self.rect.topleft = self._position

    def move_back(self, dt):
        """If called after an update, the sprite can move back"""
        self._position = self._old_position
        self.rect.topleft = self._position


class QuestGame(pgz.Scene):
    def __init__(self, map):
        self.map = map

        self.hero = Hero()
        # put the hero in the center of the map
        self.hero.position = self.map.get_center()
        self.hero._position[0] += 600
        self.hero._position[1] += 400

        # add our hero to the group
        self.map.add_sprite(self.hero)

    def draw(self, surface):

        # center the map/screen on our Hero
        self.map.set_center(self.hero.rect.center)

        self.map.draw(surface)

    def update(self, dt):
        """Tasks that occur over time should be handled here"""
        self.map.update(dt)

        # check if the sprite's feet are colliding with wall
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail
        if self.map.collide(self.hero):
            self.hero.move_back(dt)

    def handle_event(self, event):
        """Handle pygame input events"""

        # this will be handled if the window is resized
        if event.type == VIDEORESIZE:
            self.map.set_size((event.w, event.h))

        if event.type == KEYDOWN:
            if event.key == K_EQUALS:
                self.map.change_zoom(0.25)

            elif event.key == K_MINUS:
                self.map.change_zoom(-0.25)


if __name__ == "__main__":

    app = pgz.Application(
        title="My First EzPyGame Application!",
        resolution=(1280, 720),
        update_rate=60,
    )

    try:
        map = ScrollMap(app.resolution, "resources/maps/default.tmx", ["Islands"])
        game = QuestGame(map)
        app.run(game)

    except Exception:
        # pygame.quit()
        raise
