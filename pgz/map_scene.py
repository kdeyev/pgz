from typing import Optional

import pygame

from .actor import Actor
from .actor_scene import ActorScene
from .screen import Screen
from .scroll_map import ScrollMap


class MapScene(ActorScene):
    """
    Scene implementation for Tiled map management.

    Extends functionality ActorScene, but in case of MapScene actors are placed on a map.
    The implementation is based on [pyscroll](https://github.com/bitcraft/pyscroll).
    A tiled map can be created and modified with wonderful [Tiled](https://www.mapeditor.org/) maps editor.

    The maps loading and usage is backed by [PyTMX](https://github.com/bitcraft/PyTMX)

    Actors also can be added to different collision groups,
    which allows easily identify collision of an actor with a specific actor group
    """

    def __init__(self, map: Optional[ScrollMap] = None):
        """
        Create a MapScene object

        The map object loading is done with the map loader (a-la pgzero resource loaders). So for loading a map from "default.tmx" file of the resource directory:
        ```
        tmx = pgz.maps.default
        map = pgz.ScrollMap(app.resolution, tmx, ["Islands"])
        ```

        Args:
            map (Optional[ScrollMap], optional): Loaded map object. Defaults to None.
        """
        super().__init__()
        # The map object used by the scene
        self._map = map
        # The central actor object. The map view will render the central actor always in the center of the screen.
        self._central_actor: Optional[Actor] = None
        # Block the underlying calls of the draw method. This one used bu multiplayer.
        self.block_draw = False
        # Block the underlying calls of the update method. This one used bu multiplayer.
        self.block_update = False

    @property
    def map(self) -> ScrollMap:
        """
        Get map object

        Returns:
            ScrollMap: the map object used by the scene
        """
        if not self._map:
            raise Exception("Map was not configured")
        return self._map

    def set_map(self, map):
        """
        Set map object

        Args:
            map ([type]): map object to set
        """
        self._map = map

    def dispatch_event(self, event: pygame.event.Event) -> None:
        """
        Overriden events dispatch method
        Used for mouse cursor position transformation into map "world coordinates"

        Args:
            event (pygame.event.Event): pygame Event object
        """
        if event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            view_pos = event.pos
            scene_pos = self.map.transform(view_pos)
            event.scene_pos = scene_pos  # type: ignore
            event.pos = scene_pos  # type: ignore
        super().dispatch_event(event)

    def update(self, dt: float) -> None:
        """
        Overriden update method
        Implementation of the update method for the MapScene.

        This method updates all the actors attached to the scene.

        Args:
            dt (float): time in milliseconds since the last update
        """
        if self.block_update:
            return

        # DO NOT CALL ActorScene.update !
        self.map.update(dt)

    def draw(self, screen: Screen) -> None:
        """
        Overriden rendering method
        Implementation of the update method for the MapScene.

        The ActorScene implementation renders all the actorts attached to the scene.

        Args:
            screen (Screen): screen to draw the scene on
        """
        if self.block_draw:
            return

        if self._central_actor:
            # center the map/screen on our Ship
            self.map.set_center(self._central_actor.pos)

        # DO NOT CALL ActorScene.draw !
        self.map.draw(screen)

    def add_actor(self, actor: Actor, central_actor: bool = False, group_name: str = "") -> None:
        """
        Overriden add_actor method
        Implementation of the add_actor method for the MapScene.

        The ActorScene implementation renders all the actorts attached to the scene.

        Args:
            actor (Actor): actor to add
            central_actor (bool, optional): Sets the actor to be central actor for the scene. The map view will be centered on the actor. Defaults to False.
            group_name (str, optional): Collision group name. Defaults to "".
        """
        super().add_actor(actor, group_name)

        if central_actor:
            if self._central_actor:
                self._central_actor.is_central_actor = False
            self._central_actor = actor
            self._central_actor.is_central_actor = True
        # add our ship to the group
        self.map.add_sprite(actor.sprite_delegate)

    def remove_actor(self, actor: Actor) -> None:
        """
        Overriden remove_actor method
        Implementation of the remove_actor method for the MapScene.

        Args:
            actor (Actor): actor to be removed
        """
        super().remove_actor(actor)
        if actor == self._central_actor:
            self._central_actor = None
        self.map.remove_sprite(actor.sprite_delegate)

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Overriden event handler
        Implementation of the event handler method for the MapScene.

        Args:
            event (pygame.event.Event): pygame event object
        """
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
        """
        Detect collision with tiles in the map object used by the scene

        Args:
            actor (Actor): actor for collision detection

        Returns:
            bool: True if the collision with map tiles is detected
        """
        return self.map.collide_map(actor.sprite_delegate)
