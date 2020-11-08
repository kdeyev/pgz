from typing import Dict, List, Optional

import pygame

from ..actor import Actor, SpriteDelegate


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
