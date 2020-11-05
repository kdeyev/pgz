import pgzero.actor
import pygame
from pygame.surface import Surface

from .rect import ZRect


class SpriteDelegate(pygame.sprite.Sprite):
    def __init__(self, actor: "Actor") -> None:
        super().__init__()
        self._actor = actor

    @property
    def rect(self) -> ZRect:
        return self._actor.rect

    @property
    def image(self) -> Surface:
        return self._actor.sprite

    def update(self, *args, **kwargs) -> None:
        return self._actor.update(*args, **kwargs)


class Actor(pgzero.actor.Actor):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._sprite: SpriteDelegate = SpriteDelegate(self)

    @property
    def rect(self) -> ZRect:
        return self._rect

    @property
    def sprite(self) -> Surface:
        return self._surf

    @property
    def sprite_delegate(self) -> SpriteDelegate:
        return self._sprite

    def draw(self, screen: Surface):
        screen.blit(self.sprite, self.topleft)
