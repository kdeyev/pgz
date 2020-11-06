from typing import Optional

import pygame

from .actor import Actor
from .scene import EventDispatcher, Scene
from .scroll_map import ScrollMap


class MapScene(Scene):
    def __init__(self, map: ScrollMap):
        super().__init__()
        self._map = map
        self.central_actor: Optional[Actor] = None

    def dispatch_event(self, event: pygame.event.Event) -> None:
        # transfrom mouse positions
        if event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            view_pos = event.pos
            scene_pos = self._map.transform(view_pos)
            event.scene_pos = scene_pos
            event.pos = scene_pos
        super().dispatch_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        if self.central_actor:
            # center the map/screen on our Ship
            self._map.set_center(self.central_actor.pos)

        self._map.draw(surface)

    def add_actor(self, actor: Actor, central_actor: bool = False) -> None:
        if central_actor:
            self.central_actor = actor
        # add our ship to the group
        self._map.add_sprite(actor.sprite_delegate)

    def remove_actor(self, actor: Actor) -> None:
        if actor == self.central_actor:
            self.central_actor = None
        self._map.remove_sprite(actor.sprite_delegate)

    @property
    def map(self) -> ScrollMap:
        return self._map
