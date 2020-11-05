import pgzero.actor
import pygame


class Sprite(pygame.sprite.Sprite):
    def __init__(self, actor) -> None:
        super().__init__()
        self._actor = actor

    @property
    def rect(self):
        return self._actor.rect

    @property
    def image(self):
        return self._actor.sprite

    def update(self, *args, **kwargs) -> None:
        return self._actor.update(*args, **kwargs)


class Actor(pgzero.actor.Actor):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._sprite = Sprite(self)

    @property
    def rect(self):
        return self._rect

    @property
    def sprite(self):
        return self._surf

    @property
    def sprite_delegate(self):
        return self._sprite

    def draw(self, screen):
        screen.blit(self.sprite, self.topleft)
