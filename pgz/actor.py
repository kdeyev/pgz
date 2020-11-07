from typing import Any, Callable, Optional, cast
from uuid import uuid4

import pgzero.actor
import pygame
from pygame.display import update

from .rect import ZRect
from .screen import Screen


class Actor(pgzero.actor.Actor):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._sprite: SpriteDelegate = SpriteDelegate(self)

        self.is_central_actor = False

        self._uuid: str
        if "uuid" in kwargs:
            self._uuid = kwargs["uuid"]
        else:
            self._uuid = str(uuid4())

        self.deleter: Optional[Callable[[Actor], None]] = None

    @property
    def uuid(self) -> str:
        return self._uuid

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

    def update(self, dt: float) -> None:
        pass


class SpriteDelegate(pygame.sprite.Sprite):
    def __init__(self, actor: Actor) -> None:
        super().__init__()
        self._actor = actor

    @property
    def actor(self) -> Actor:
        return self._actor

    @property
    def rect(self) -> Optional[pygame.rect.Rect]:  # type: ignore
        return self._actor.rect

    @property
    def image(self) -> Optional[pygame.surface.Surface]:  # type: ignore
        return self._actor.sprite

    def update(self, *args: Any, **kwargs: Any) -> None:
        self._actor.update(*args, **kwargs)
