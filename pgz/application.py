import asyncio
import concurrent.futures
import sys
from typing import Optional, Tuple

import pygame
from asgiref.sync import sync_to_async

#
from pgz.scene import Scene

from .clock import Clock, global_clock
from .keyboard import Keyboard
from .screen import Screen
from .utils.fps_calc import FPSCalc


class Application:
    """
    The idea and the original code was taken from [EzPyGame](https://github.com/Mahi/EzPyGame)

    A simple wrapper around `pygame` for running games easily.

    Also makes scene management seamless together with the `Scene` class.
    """

    def __init__(self, title: Optional[str], resolution: Optional[Tuple[int, int]], update_rate: Optional[int] = None):
        """
        Create an instance of the pgz.Application

        Args:
            title (Optional[str]): title to display in the window's title bar
            resolution (Optional[Tuple[int, int]]): resolution of the game window
            update_rate (Optional[int], optional): how many times per second to update. Defaults to None.


        If any parameters are left to `None`, these settings must be
        defined either manually through `application.<setting> = value`
        or via `Scene`'s class variable settings.

        Examples:
        ```
            class Menu(pgz.Scene):
                ...

            class Game(pgz.Scene):
                ...

            app = pgz.Application(
                title='My First Application',
                resolution=(1280, 720),
                update_rate=60,
            )
            main_menu = Menu()
            app.run(main_menu)
        ```
        """
        pygame.init()
        self._update_rate = update_rate
        self._scene = None

        self._keyboard = Keyboard()

        # Trigger property setters
        self.title = title
        self.resolution = resolution

    @property
    def title(self) -> str:
        """Get application title

        Returns:
            str: application title
        """
        return pygame.display.get_caption()[0]

    @title.setter
    def title(self, value: str) -> None:
        """Change application title

        Args:
            value (str): application title to set
        """
        pygame.display.set_caption(value)

    @property
    def resolution(self) -> Tuple[int, int]:
        """Get application screen resolution

        Returns:
            Tuple[int, int]: application screen resolution
        """
        return (self._screen.width, self._screen.height)

    @resolution.setter
    def resolution(self, value: Tuple[int, int]) -> None:
        """Change application screen resolution

        Args:
            value (Tuple[int, int]): application screen resolution to use
        """
        self._screen = Screen(pygame.display.set_mode(value))

    @property
    def update_rate(self) -> int:
        """Get application update rate

        Returns:
            int: application update rate
        """
        return self._update_rate

    @update_rate.setter
    def update_rate(self, value: int) -> None:
        """Change application update rate

        Args:
            value (int): application update rate to set
        """
        self._update_rate = value

    @property
    def screen(self) -> Screen:
        """Get application screen object

        Returns:
            Screen: application screen object
        """
        return self._screen

    @property
    def keyboard(self) -> Keyboard:
        """
        Get `Keyboard` object.

        Returns:
            Keyboard: keyboard object
        """
        return self._keyboard

    @property
    def clock(self) -> Clock:
        """
        Get `Clock` object.

        Actually returns the global clock object.

        Returns:
            Clock: clock object
        """
        return global_clock

    @property
    def active_scene(self) -> Optional[Scene]:
        """
        Get currently active scene.

        Can be `None`.

        Returns:
            Optional[Scene]: currently active scene
        """
        return self._scene

    def change_scene(self, scene: Optional[Scene]) -> None:
        """
        Change the currently active scene.

        This will invoke `Scene.on_exit` and
        `Scene.on_enter` methods on the switching scenes.

        If `None` is provided, the application's execution will end.

        Args:
            scene (Optional[Scene]): the scene to change into
        """
        if self.active_scene is not None:
            self.active_scene.on_exit(next_scene=scene)
            self.active_scene._application = None
        self._scene, old_scene = scene, self.active_scene
        if self.active_scene is not None:
            self.active_scene._application = self
            self.active_scene.on_enter(previous_scene=old_scene)

    def _draw(self) -> None:
        if self.active_scene:
            self.active_scene.draw(self._screen)

    def _update(self, dt: float) -> None:
        if self.active_scene:
            self.active_scene.update(dt)

    def _handle_event(self, event: pygame.event.Event) -> None:
        if self.active_scene:
            self.active_scene.dispatch_event(event)

    def run(self, scene: Optional[Scene] = None) -> None:
        """
        Execute the application.

        Args:
            scene (Optional[Scene], optional): scene to start the execution from. Defaults to None.
        """
        if scene is None:
            if self.active_scene is None:
                raise ValueError("No scene provided")
        else:
            self.change_scene(scene)

        try:
            asyncio.get_event_loop().run_until_complete(self.run_as_coroutine())
        finally:
            asyncio.get_event_loop().close()

    async def run_as_coroutine(self) -> None:
        self.running = True
        try:
            await self._mainloop()
        finally:
            pygame.display.quit()
            pygame.mixer.quit()
            self.running = False

    async def _mainloop(self) -> None:
        """
        Run the main loop of Pygame Zero.
        """
        clock = pygame.time.Clock()
        fps_calc = FPSCalc()

        fps = 0.0
        # self.need_redraw = True
        while True:
            self._screen.clear()

            dt = clock.tick(self._update_rate) / 1000

            # TODO: Use asyncio.sleep() for frame delay if accurate enough
            await asyncio.sleep(0)
            event: pygame.event.Event
            for event in pygame.event.get():

                if event.type == pygame.VIDEORESIZE:
                    self.resolution = (event.w, event.h)

                if event.type == pygame.QUIT:
                    self.change_scene(None)  # Trigger Scene.on_exit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q and event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META):
                        sys.exit(0)
                    self.keyboard._press(event.key)
                elif event.type == pygame.KEYUP:
                    self.keyboard._release(event.key)

                self._handle_event(event)

            global_clock.tick(dt)
            fps_calc.push(1.0 / dt)
            if fps_calc.counter == 100:
                fps = fps_calc.aver()
                print(f"fps {fps}")

            await sync_to_async(self._update)(dt)
            await sync_to_async(self._draw)()

            self._screen.draw.text(f"FPS: {fps}", pos=(0, 0))

            pygame.display.update()
