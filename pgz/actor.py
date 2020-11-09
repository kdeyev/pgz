import json
from typing import Any, Callable, Dict, Optional, cast
from uuid import uuid4

import pgzero
import pgzero.actor
import pygame

from .screen import Screen


class BaseActor(pgzero.actor.Actor):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._sprite: SpriteDelegate = SpriteDelegate(self)

        self.is_central_actor = False
        self.scene_uuid: str = ""

        self._uuid: str
        if "uuid" in kwargs:
            self._uuid = kwargs["uuid"]
        else:
            self._uuid = str(uuid4())

        self.deleter: Optional[Callable[[BaseActor], None]] = None

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
    def __init__(self, actor: BaseActor) -> None:
        super().__init__()
        self._actor = actor

    @property
    def actor(self) -> BaseActor:
        return self._actor

    @property
    def rect(self) -> Optional[pygame.rect.Rect]:  # type: ignore
        return self._actor.rect

    @property
    def image(self) -> Optional[pygame.surface.Surface]:  # type: ignore
        return self._actor.sprite

    def update(self, *args: Any, **kwargs: Any) -> None:
        self._actor.update(*args, **kwargs)


class Actor(BaseActor):
    """
    The main Actor API is inspired from [pgzero.Actor](https://pygame-zero.readthedocs.io/en/stable/builtins.html#actors)
    """

    # DELEGATED_ATTRIBUTES = [a for a in dir(Actor) if not a.startswith("_")] + Actor.DELEGATED_ATTRIBUTES
    ATTRIBUTES_TO_TRACK = BaseActor.DELEGATED_ATTRIBUTES + ["angle", "image"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.scene_uuid: str = ""
        self._incremental_changes = {}

        self.keyboard = None
        self.accumulate_changes = True
        # self._on_prop_change: Optional[Callable[[UUID, str, Any], None]] = None

    def __setattr__(self, attr: str, value: Any) -> None:
        if attr in self.__class__.ATTRIBUTES_TO_TRACK and hasattr(self, "accumulate_changes") and self.accumulate_changes:
            if getattr(self, attr) != value:
                self._incremental_changes[attr] = value
                # self._on_prop_change(self.uuid, attr, value)

        super().__setattr__(attr, value)

    def get_incremental_changes(self):
        incremental_changes = self._incremental_changes
        self._incremental_changes = {}
        return incremental_changes

    def serialize_state(self) -> Dict[str, Any]:
        state = {}
        for attr in self.__class__.ATTRIBUTES_TO_TRACK:
            try:
                value = getattr(self, attr)
            except Exception as e:
                print(f"MultiplayerActor.serialize_state: {e}")
                continue

            try:
                json.dumps({attr: value})
            except Exception as e:
                print(f"MultiplayerActor.serialize_state: {e}")
                continue

            state[attr] = value
        return state
