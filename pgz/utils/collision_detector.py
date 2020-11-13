from typing import Dict, List, Optional

import pygame

from ..actor import Actor


class CollisionDetector(object):
    """Class helper for easier collision detection

    The class manages multiple collision groups and can detect a collsion with each one of groups independently.
    """

    def __init__(self) -> None:
        """Create a collision detecor"""

        # Collision groups
        self._groups: Dict[str, pygame.sprite.Group] = {}
        # List of all known actors
        self._actors = {}

    def add_actor(self, actor: Actor, group_name: str = "") -> None:
        """Add an actor to the detector

        Args:
            actor (Actor): actor to add
            group_name (str, optional): collision group to use. Defaults to "".
        """
        self._actors[actor.uuid] = actor
        self._add_sprite(actor.sprite_delegate, group_name)

    def remove_actor(self, actor: Actor) -> None:
        """Remore an actor from the detector and all collision groups

        Args:
            actor (Actor): actor to remove
        """
        del self._actors[actor.uuid]
        self._remove_sprite(actor.sprite_delegate)

    def get_actor(self, uuid: str) -> Actor:
        """Get actor by UUID

        Args:
            uuid (str): UUID of the actor

        Returns:
            Actor: actor associated with the UUID
        """
        return self._actors[uuid]

    def get_actors(self) -> List[Actor]:
        """Get list of all the known actors.

        Returns:
            List[Actor]: list of actors
        """
        return list(self._actors.values())

    def _add_sprite(self, sprite: pygame.sprite.Sprite, group_name: str = "") -> None:
        if group_name not in self._groups:
            self._groups[group_name] = pygame.sprite.Group()
        self._groups[group_name].add(sprite)

    def _remove_sprite(self, sprite: pygame.sprite.Sprite) -> None:
        for group in self._groups.values():
            group.remove(sprite)

    def collide_group(self, sprite: pygame.sprite.Sprite, group_name: str = "") -> Optional[pygame.sprite.Sprite]:
        """Detect a collision of an actor with a specified collsion group.

        Args:
            sprite (pygame.sprite.Sprite): actor to use for collision detection.
            group_name (str, optional): collision group name. Defaults to "".

        Returns:
            Optional[pygame.sprite.Sprite]: actor was found in the collsion group.
        """
        if group_name not in self._groups:
            return None

        collision = pygame.sprite.spritecollideany(sprite, self._groups[group_name])
        return collision
