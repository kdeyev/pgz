from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple
from uuid import uuid4

import pygame

from .clock import Clock, clock
from .keyboard import Keyboard
from .screen import Screen
from .utils.event_dispatcher import EventDispatcher

if TYPE_CHECKING:
    from .application import Application


class Scene(EventDispatcher):
    """
    The idea and the original code was taken from [EzPyGame](https://github.com/Mahi/EzPyGame)

    An isolated scene which can be ran by an application.

    Create your own scene by subclassing and overriding any methods.

    Example:
    ```
    class Menu(Scene):

        def __init__(self):
            self.font = pygame.font.Font(...)

        def on_enter(self, previous_scene):
            self.title = 'Main Menu'
            self.resolution = (640, 480)
            self.update_rate = 30

        def draw(self, screen):
            pygame.draw.rect(...)
            text = self.font.render(...)
            screen.blit(text, ...)

        def handle_event(self, event):
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    game_size = self._get_game_size(event.pos)
                    self.change_scene(Game(game_size))

        def _get_game_size(self, mouse_pos_upon_click):
            ...


    class Game(pgz.Scene):
        title = 'The Game!'
        resolution = (1280, 720)
        update_rate = 60

        def __init__(self, size):
            super().__init__()
            self.size = size
            self.player = ...
            ...

        def on_enter(self, previous_scene):
            super().on_enter(previous_scene)
            self.previous_scene = previous_scene

        def draw(self, screen):
            self.player.draw(screen)
            for enemy in self.enemies:
                ...

        def update(self, dt):
            self.player.move(dt)
            ...
            if self.player.is_dead():
                self.change_scene(self.previous_scene)
            elif self.player_won():
                self.change_scene(...)

        def handle_event(self, event):
            ...  # Player movement etc.
    ```

    The above two classes use different approaches for changing
    the application's settings when the scene is entered:

    1. Manually set them in `on_enter`, as seen in `Menu`
    2. Use class variables, as I did with `Game`

    When using class variables (2), you can leave out any setting
    (defaults to `None`) to not override that particular setting.
    If you override `on_enter` in the subclass, you must call
    `super().on_enter(previous_scene)` to use the class variables.

    These settings can further be overridden in individual instances:

    ```
        my_scene0 = MyScene()
        my_scene0.resolution = (1280, 720)
        my_scene1 = MyScene(title='My Second Awesome Scene')
    ```

    Example:
    Shortcuts foe event gandling while `Scene` subclassing.
    ```
    def on_mouse_up(self, pos, button):
        # Override this for easier events handling.
        pass

    def on_mouse_down(self, pos, button):
        # Override this for easier events handling.
        pass

    def on_mouse_move(self, pos):
        # Override this for easier events handling.
        pass

    def on_key_down(self, key):
        # Override this for easier events handling.
        pass

    def on_key_up(self, key):
        # Override this for easier events handling.
        pass
    ```
    """

    _title: Optional[str] = None
    _resolution: Optional[Tuple[int, int]] = None
    _update_rate: Optional[int] = None

    def __init__(self, title: Optional[str] = None, resolution=None, update_rate: Optional[int] = None) -> None:
        self._application: Optional["Application"] = None
        if title is not None:
            self._title = title
        if resolution is not None:
            self._resolution = resolution
        if update_rate is not None:
            self._update_rate = update_rate

        self._keyboard = Keyboard()

        # Client data is the data was provided by the client during the handshake: it's usually stuff like player name, avatar, etc
        self._client_data: Dict[str, Any] = {}

        # The scene UUID is used for communication
        self._scene_uuid = str(uuid4())

    @property
    def scene_uuid(self) -> str:
        """
        Get scene UUID.
        """
        return self._scene_uuid

    def set_client_data(self, client_data: Dict[str, Any]) -> None:
        self._client_data = client_data

    @property
    def client_data(self) -> Dict[str, Any]:
        """
        Get data provided by client side.
        """
        return self._client_data

    def change_scene(self, new_scene: Optional["Scene"]) -> None:
        if not self._application:
            raise Exception("Application was not configured properly.")
        self._application.change_scene(new_scene)

    @property
    def title(self) -> str:
        """Get application title

        Returns:
            str: application title
        """
        if not self._application:
            raise Exception("Application was not configured properly.")
        return self._application.title

    @title.setter
    def title(self, value: str) -> None:
        """Change application title

        Args:
            value (str): application title to set
        """
        if not self._application:
            print("Warning: application was not configured - 'title' setting was ignored")
            return
        self._application.title = value

    @property
    def resolution(self) -> Tuple[int, int]:
        """Get application screen resolution

        Returns:
            Tuple[int, int]: application screen resolution
        """
        if not self._application:
            raise Exception("Application was not configured properly.")
        return self._application.resolution

    @resolution.setter
    def resolution(self, value: Tuple[int, int]) -> None:
        """Change application screen resolution

        Args:
            value (Tuple[int, int]): application screen resolution to use
        """
        if not self._application:
            print("Warning: application was not configured - 'resolution' setting was ignored")
            return
        self._application.resolution = value

    @property
    def update_rate(self) -> int:
        """Get application update rate

        Returns:
            int: application update rate
        """
        if not self._application:
            raise Exception("Application was not configured properly.")
        return self._application.update_rate

    @update_rate.setter
    def update_rate(self, value: int) -> None:
        """Change application update rate

        Args:
            value (int): application update rate to set
        """
        if not self._application:
            print("Warning: application was not configured - 'update_rate' setting was ignored")
            return
        self._application.update_rate = value

    @property
    def clock(self) -> Clock:
        """
        Get `Clock` object.

        Actually returns the global clock object.

        Returns:
            Clock: clock object
        """
        return clock

    @property
    def keyboard(self) -> Keyboard:
        """
        Get `Keyboard` object.

        Returns:
            Keyboard: keyboard object
        """
        return self._keyboard

    def draw(self, screen: Screen) -> None:
        """
        Override this with the scene drawing.

         Args:
            screen (Screen): screen to draw the scene on
        """

    def update(self, dt: float) -> None:
        """
        Override this with the scene update tick.

        Args:
            dt (float): time in milliseconds since the last update
        """

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Override this to handle an event in the scene.

        All of `pygame`'s events are sent here, so filtering
        should be applied manually in the subclass.

        Args:
            event (pygame.event.Event): event to handle
        """

        if event.type == pygame.KEYDOWN:
            self._keyboard._press(event.key)
        elif event.type == pygame.KEYUP:
            self._keyboard._release(event.key)

    def on_enter(self, previous_scene: Optional["Scene"]) -> None:
        """
        Override this to initialize upon scene entering.

        If you override this method and want to use class variables
        to change the application's settings, you must call
        ``super().on_enter(previous_scene)`` in the subclass.

        Args:
            previous_scene (Optional[Scene]): previous scene was running
        """
        for attr in ("_title", "_resolution", "_update_rate"):
            value = getattr(self, attr)
            if value is not None:
                if self._application is None:
                    print(f"Warning: application was not configured - '{attr}' setting was ignored")
                    continue
                setattr(self._application, attr.lower(), value)

        # Set event dispatcher
        self.load_handlers()

    def on_exit(self, next_scene: Optional["Scene"]) -> None:
        """
        Override this to deinitialize upon scene exiting.

        Args:
            next_scene (Optional[Scene]): next scene to run
        """
