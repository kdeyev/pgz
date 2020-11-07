from typing import Dict, List, Optional
from uuid import uuid4

import pygame

from .actor import Actor, SpriteDelegate
from .scene import Scene
from .screen import Screen


class CollisionDetector(object):
    def __init__(self) -> None:
        self._groups: Dict[str, pygame.sprite.Group] = {}
        self._actors = {}

    def add_actor(self, actor: Actor, group_name: str = "") -> None:
        self._actors[actor.uuid] = actor
        self._add_sprite(actor.sprite_delegate, group_name)

    def remove_actor(self, actor: Actor) -> None:
        del self._actors[actor.uuid]
        self._remove_sprite(actor.sprite_delegate)

    def get_actor(self, uuid: str) -> Actor:
        return self._actors[uuid]

    def get_actors(self) -> List[Actor]:
        return list(self._actors.values())

    def _add_sprite(self, sprite: pygame.sprite.Sprite, group_name: str = "") -> None:
        if group_name not in self._groups:
            self._groups[group_name] = pygame.sprite.Group()
        self._groups[group_name].add(sprite)

    def _remove_sprite(self, sprite: pygame.sprite.Sprite) -> None:
        for group in self._groups.values():
            group.remove(sprite)

    def collide_group(self, sprite: pygame.sprite.Sprite, group_name: str = "") -> Optional[pygame.sprite.Sprite]:
        if group_name not in self._groups:
            return None

        collision = pygame.sprite.spritecollideany(sprite, self._groups[group_name])
        return collision


class ActorScene(Scene):
    def __init__(self) -> None:
        super().__init__()
        self._actors: Dict[str, Actor] = {}
        self._collaider = CollisionDetector()
        # The scene UUID is used for communication
        self._scene_uuid = str(uuid4())
        self.accumulate_changes = False

    @property
    def scene_uuid(self) -> str:
        """
        Get client UUID.
        """
        return self._scene_uuid

    def set_collaider(self, collaider: CollisionDetector):
        self._collaider = collaider

    def draw(self, surface: Screen) -> None:
        for actor in self._actors.values():
            actor.draw(surface)

    def add_actor(self, actor: Actor, group_name: str = "") -> None:
        actor.accumulate_changes = self.accumulate_changes
        actor.keyboard = self.keyboard
        actor.scene_uuid = self.scene_uuid
        self._actors[actor.uuid] = actor
        self._collaider.add_actor(actor, group_name)
        actor.deleter = self.remove_actor

    def remove_actor(self, actor: Actor) -> None:
        del self._actors[actor.uuid]
        self._collaider.remove_actor(actor)

    def remove_actors(self) -> None:
        uuids = [uuid for uuid in self._actors.keys()]
        for uuid in uuids:
            self.remove_actor(self._actors[uuid])

    def get_actor(self, uuid: str) -> Actor:
        return self._actors[uuid]

    def get_actors(self) -> List[Actor]:
        return list(self._actors.values())

    def update(self, dt: float) -> None:
        for actor in self._actors.values():
            actor.update(dt)

    def collide_group(self, sprite: pygame.sprite.Sprite, group_name: str = "") -> Optional[pygame.sprite.Sprite]:
        sprite_deleg: SpriteDelegate = self._collaider.collide_group(sprite, group_name)
        if sprite_deleg:
            return sprite_deleg.actor
        return None
