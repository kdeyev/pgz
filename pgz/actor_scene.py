from typing import Dict, List, Optional

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
    """
    Scene implementation for management of multiple actors.

    Actors also can be added to different collision groups,
    which allows easily identify collision of an actor with a specific actor group
    """

    def __init__(self) -> None:
        super().__init__()
        # Actors dict
        self._actors: Dict[str, Actor] = {}
        # Collsion detector for management of different collision groups
        self._collision_detector = CollisionDetector()
        # Notifies all the actors that accumulation of incremental changes is required. This one used bu multiplayer.
        self.accumulate_changes = False

    def set_collision_detector(self, collision_detector: CollisionDetector):
        """Set external collsinion detector object.

        The default collision detector can be use in the most of the cases.
        This method in used by multiplayer.
        """
        self._collision_detector = collision_detector

    def draw(self, surface: Screen) -> None:
        """Override this with the scene drawing.

        The ActorScene implementation renders all the actorts attached to the scene.

        :param pgz.Screen screen: screen to draw the scene on
        """
        for actor in self._actors.values():
            actor.draw(surface)

    def add_actor(self, actor: Actor, group_name: str = "") -> None:
        """
        Add actor to the scene and add the actor to the collision group.
        """

        # Notify actor that accumulation of incremental changes is required. This one used bu multiplayer.
        actor.accumulate_changes = self.accumulate_changes

        # Set keyboard object to the actor. For your convenience
        actor.keyboard = self.keyboard
        # Set scene UUID to the actor. This one used bu multiplayer.
        actor.scene_uuid = self.scene_uuid
        # Add actor to a dict
        self._actors[actor.uuid] = actor
        # Add actor to collision detector with collision group name
        self._collision_detector.add_actor(actor, group_name)
        # Add deleter callback to the actor. This one is used for actor's suicide
        actor.deleter = self.remove_actor

    def remove_actor(self, actor: Actor) -> None:
        """Remove actor from the scene.

        Actor also will be removed from the associated collision detector

        Args:
            actor (Actor): Actor to be removed
        """

        del self._actors[actor.uuid]
        self._collision_detector.remove_actor(actor)

    def remove_actors(self) -> None:
        """Revome all actors from the scene and the associated collision detector"""
        uuids = [uuid for uuid in self._actors.keys()]
        for uuid in uuids:
            self.remove_actor(self._actors[uuid])

    def get_actor(self, uuid: str) -> Actor:
        """Get actor object by its UUID

        Args:
            uuid (str): UUID of the actor to be retrieved

        Returns:
            Actor: Actor associated with the UUID
        """
        return self._actors[uuid]

    def get_actors(self) -> List[Actor]:
        """Get list of actors

        Returns:
            List[Actor]: The list of actors on the scene
        """
        return list(self._actors.values())

    def update(self, dt: float) -> None:
        for actor in self._actors.values():
            actor.update(dt)

    def collide_group(self, sprite: pygame.sprite.Sprite, group_name: str = "") -> Optional[pygame.sprite.Sprite]:
        sprite_deleg: SpriteDelegate = self._collision_detector.collide_group(sprite, group_name)
        if sprite_deleg:
            return sprite_deleg.actor
        return None
