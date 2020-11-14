from typing import Dict, List, Optional

from ..actor import Actor, SpriteDelegate
from ..scene import Scene
from ..screen import Screen
from ..utils.collision_detector import CollisionDetector


class ActorScene(Scene):
    """
    Scene implementation for management of multiple actors.

    Actors also can be added to different collision groups, which allows easily identify collision of an actor with a specific actor group.
    """

    def __init__(self) -> None:
        """
        Create an ActorScene object
        """
        super().__init__()
        # Actors dict
        self._actors: Dict[str, Actor] = {}
        # Collsion detector for management of different collision groups
        self._collision_detector = CollisionDetector()
        # Notifies all the actors that accumulation of incremental changes is required. This one used bu multiplayer.
        self.accumulate_changes = False

    def set_collision_detector(self, collision_detector: CollisionDetector):
        """
        Set external collsinion detector object.

        The default collision detector can be use in the most of the cases.
        This method in used by multiplayer.
        """

        self._collision_detector = collision_detector

    def add_actor(self, actor: Actor, group_name: str = "") -> None:
        """
        Add actor to the scene and add the actor to the collision group.

        Args:
            actor (Actor): actor to add
            group_name (str, optional): Collision group name. Defaults to "".
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
        """
        Remove actor from the scene.

        Actor also will be removed from the associated collision detector

        Args:
            actor (Actor): Actor to be removed
        """

        del self._actors[actor.uuid]
        self._collision_detector.remove_actor(actor)

    def remove_actors(self) -> None:
        """
        Remove all actors from the scene and the associated collision detector
        """
        uuids = [uuid for uuid in self._actors.keys()]
        for uuid in uuids:
            self.remove_actor(self._actors[uuid])

    def get_actor(self, uuid: str) -> Actor:
        """
        Get actor object by its UUID

        Args:
            uuid (str): UUID of the actor to be retrieved

        Returns:
            Actor: Actor associated with the UUID
        """
        return self._actors[uuid]

    def get_actors(self) -> List[Actor]:
        """
        Get list of actors

        Returns:
            List[Actor]: The list of actors on the scene
        """
        return list(self._actors.values())

    def collide_group(self, actor: Actor, group_name: str = "") -> Optional[Actor]:
        """
        Detect collision of a ginen actor with the actors in requested collsion group.

        Args:
            actor (Actor): actor to detect collisions with
            group_name (str, optional): Collision group name. Defaults to "".

        Returns:
            Optional[Actor]: A collins actor in the specified collision group
        """
        sprite_deleg: SpriteDelegate = self._collision_detector.collide_group(actor, group_name)
        if sprite_deleg:
            return sprite_deleg.actor
        return None

    def draw(self, surface: Screen) -> None:
        """
        Overriden rendering method

        Implementation of the update method for the ActorScene.

        The ActorScene implementation renders all the actorts attached to the scene.

        Args:
            screen (Screen): screen to draw the scene on
        """

        for actor in self._actors.values():
            actor.draw(surface)

    def update(self, dt: float) -> None:
        """
        Overriden update method

        Implementation of the update method for the ActorScene.

        This method updates all the actors attached to the scene.

        Args:
            dt (float): time in milliseconds since the last update
        """

        for actor in self._actors.values():
            actor.update(dt)
