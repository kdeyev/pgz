import pygame
from pygame.locals import K_DOWN, K_EQUALS, K_ESCAPE, K_LEFT, K_MINUS, K_RIGHT, K_UP, KEYDOWN, QUIT, VIDEORESIZE

from map import ScrollMap

HERO_MOVE_SPEED = 200  # pixels per second


# simple wrapper to keep the screen resizeable
def init_screen(width, height):
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    return screen


# make loading images a little easier
def load_image(filename):
    return pygame.image.load(filename)


class Hero(pygame.sprite.Sprite):
    """Our Hero
    The Hero has three collision rects, one for the whole sprite "rect" and
    "old_rect", and another to check collisions with walls, called "feet".
    The position list is used because pygame rects are inaccurate for
    positioning sprites; because the values they get are 'rounded down'
    as integers, the sprite would move faster moving left or up.
    Feet is 1/2 as wide as the normal rect, and 8 pixels tall.  This size size
    allows the top of the sprite to overlap walls.  The feet rect is used for
    collisions, while the 'rect' rect is used for drawing.
    There is also an old_rect that is used to reposition the sprite if it
    collides with level walls.
    """

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
        self._position[0] += self.velocity[0] * dt
        self._position[1] += self.velocity[1] * dt
        self.rect.topleft = self._position

    def move_back(self, dt):
        """If called after an update, the sprite can move back"""
        self._position = self._old_position
        self.rect.topleft = self._position


class QuestGame(object):
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

    def handle_input(self):
        """Handle pygame input events"""
        poll = pygame.event.poll

        event = poll()
        while event:
            if event.type == QUIT:
                self.running = False
                break

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                    break

                elif event.key == K_EQUALS:
                    self.map.change_zoom(0.25)

                elif event.key == K_MINUS:
                    self.map.change_zoom(-0.25)

            # this will be handled if the window is resized
            elif event.type == VIDEORESIZE:
                init_screen(event.w, event.h)
                self.map.set_size((event.w, event.h))

            event = poll()

        # using get_pressed is slightly less accurate than testing for events
        # but is much easier to use.
        pressed = pygame.key.get_pressed()
        if pressed[K_UP]:
            self.hero.velocity[1] = -HERO_MOVE_SPEED
        elif pressed[K_DOWN]:
            self.hero.velocity[1] = HERO_MOVE_SPEED
        else:
            self.hero.velocity[1] = 0

        if pressed[K_LEFT]:
            self.hero.velocity[0] = -HERO_MOVE_SPEED
        elif pressed[K_RIGHT]:
            self.hero.velocity[0] = HERO_MOVE_SPEED
        else:
            self.hero.velocity[0] = 0

    def run(self):
        """Run the game loop"""
        clock = pygame.time.Clock()
        self.running = True

        from collections import deque

        times = deque(maxlen=30)

        try:
            while self.running:
                dt = clock.tick() / 1000.0
                times.append(clock.get_fps())
                # print(sum(times)/len(times))

                self.handle_input()
                self.update(dt)
                self.draw(screen)
                pygame.display.flip()

        except KeyboardInterrupt:
            self.running = False


if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    screen = init_screen(1600, 1200)
    pygame.display.set_caption("Quest - An epic journey.")

    try:
        map = ScrollMap(screen, "resources/maps/default.tmx", ["Islands"])
        game = QuestGame(map)
        game.run()
    except Exception:
        pygame.quit()
        raise
