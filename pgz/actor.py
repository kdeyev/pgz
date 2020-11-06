from typing import Any, Optional, cast

import pgzero.actor
import pygame
from pgzero.screen import Screen

from .rect import ZRect

# from pygame import Rect
# from pygame.surface import Surface


class Actor(pgzero.actor.Actor):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._sprite: SpriteDelegate = SpriteDelegate(self)

    @property
    def rect(self) -> Optional[pygame.rect.Rect]:
        return cast(pygame.rect.Rect, self._rect)

    @property
    def sprite(self) -> pygame.surface.Surface:
        return cast(pygame.surface.Surface, self._surf)

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
    def rect(self) -> Optional[pygame.rect.Rect]:  # type: ignore
        return self._actor.rect

    @property
    def image(self) -> Optional[pygame.surface.Surface]:  # type: ignore
        return self._actor.sprite

    def update(self, *args: Any, **kwargs: Any) -> None:
        self._actor.update(*args, **kwargs)
