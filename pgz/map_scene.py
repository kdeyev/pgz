from typing import Dict, Optional

import pygame

from .actor import Actor
from .actor_scene import ActorScene
from .screen import Screen
from .scroll_map import ScrollMap


class MapScene(ActorScene):
    def __init__(self, map: Optional[ScrollMap] = None):
        super().__init__()
        self._map = map
        self.central_actor: Optional[Actor] = None

    def dispatch_event(self, event: pygame.event.Event) -> None:
        # transfrom mouse positions
        if event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            view_pos = event.pos
            scene_pos = self.map.transform(view_pos)
            event.scene_pos = scene_pos  # type: ignore
            event.pos = scene_pos  # type: ignore
        super().dispatch_event(event)

    def draw(self, surface: Screen) -> None:
        # DO NOT CALL ActorScene.draw !

        if self.central_actor:
            # center the map/screen on our Ship
            self.map.set_center(self.central_actor.pos)

        self.map.draw(surface)

    def add_actor(self, actor: Actor, central_actor: bool = False, group_name: str = "") -> None:
        super().add_actor(actor, group_name)

        if central_actor:
            self.central_actor = actor
        # add our ship to the group
        self.map.add_sprite(actor.sprite_delegate)

    def remove_actor(self, actor: Actor) -> None:
        super().remove_actor(actor)
        if actor == self.central_actor:
            self.central_actor = None
        self.map.remove_sprite(actor.sprite_delegate)

    @property
    def map(self) -> ScrollMap:
        if not self._map:
            raise Exception("Map was not configured")
        return self._map

    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)

        # this will be handled if the window is resized
        if event.type == pygame.VIDEORESIZE:
            self.map.set_size((event.w, event.h))
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_EQUALS:
                self.map.change_zoom(0.25)
            elif event.key == pygame.K_MINUS:
                self.map.change_zoom(-0.25)

    def collide_map(self, actor: Actor) -> bool:
        return self.map.collide_map(actor.sprite_delegate)
