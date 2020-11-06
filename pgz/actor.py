from typing import Any

import pgzero.actor
import pygame
from pgzero.screen import Screen
from pygame.surface import Surface

from .rect import ZRect


class Actor(pgzero.actor.Actor):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._sprite: SpriteDelegate = SpriteDelegate(self)

    @property
    def rect(self) -> ZRect:
        return self._rect

    @property
    def sprite(self) -> pygame.sprite.Sprite:
        return self._surf

    @property
    def sprite_delegate(self) -> "SpriteDelegate":
        return self._sprite

    def draw(self, screen: Screen) -> None:
        screen.blit(self.sprite, self.topleft)


class SpriteDelegate(pygame.sprite.Sprite):
    def __init__(self, actor: Actor) -> None:
        super().__init__()
        self._actor = actor

    @property
    def rect(self) -> ZRect:
        return self._actor.rect

    @property
    def image(self) -> pygame.sprite.Sprite:
        return self._actor.sprite

    def update(self, *args: Any, **kwargs: Any) -> None:
        self._actor.update(*args, **kwargs)
