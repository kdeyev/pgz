import asyncio
import sys
from typing import Optional, Tuple

import pygame

#
from pgz.scene import Scene

from .clock import Clock, global_clock
from .keyboard import keyboard
from .screen import Screen
from .utils.fps_calc import FPSCalc


class Application:
    """
    The idea and the original code was taken from EzPyGame:
    https://github.com/Mahi/EzPyGame

    A simple wrapper around :mod:`pygame` for running games easily.

    Also makes scene management seamless together with
    the :class:`.Scene` class.

    :param str|None title: title to display in the window's title bar
    :param tuple[int,int]|None resolution: resolution of the game window
    :param int|None update_rate: how many times per second to update

    If any parameters are left to ``None``, these settings must be
    defined either manually through ``application.<setting> = value``
    or via :class:`.Scene`'s class variable settings.

    Example usage:

    .. code-block:: python

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
    """

    def __init__(self, title: str, resolution: Tuple[int, int], update_rate: Optional[int] = None):
        pygame.init()
        self.update_rate = update_rate
        self._scene = None

        self.keyboard = keyboard

        # Trigger property setters
        self.title = title
        self.resolution = resolution

    @property
    def title(self) -> str:
        return pygame.display.get_caption()[0]

    @title.setter
    def title(self, value: str) -> None:
        pygame.display.set_caption(value)

    @property
    def screen(self) -> Screen:
        return self._screen

    @property
    def clock(self) -> Clock:
        return global_clock

    @property
    def resolution(self) -> Tuple[int, int]:
        return (self._screen.width, self._screen.height)

    @resolution.setter
    def resolution(self, value: Tuple[int, int]) -> None:
        self._screen = Screen(pygame.display.set_mode(value))

    @property
    def active_scene(self) -> Optional[Scene]:
        """The currently active scene. Can be ``None``."""
        return self._scene

    def change_scene(self, scene: Optional[Scene]) -> None:
        """Change the currently active scene.

        This will invoke :meth:`.Scene.on_exit` and
        :meth:`.Scene.on_enter` methods on the switching scenes.

        If ``None`` is provided, the application's execution will end.

        :param Scene|None scene: the scene to change into
        """
        if self.active_scene is not None:
            self.active_scene.on_exit(next_scene=scene)
            self.active_scene._application = None
        self._scene, old_scene = scene, self.active_scene
        if self.active_scene is not None:
            self.active_scene._application = self
            self.active_scene.on_enter(previous_scene=old_scene)

    def draw(self) -> None:
        if self.active_scene:
            self.active_scene.draw(self._screen)

    def update(self, dt: float) -> None:
        if self.active_scene:
            self.active_scene.update(dt)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.active_scene:
            self.active_scene.dispatch_event(event)

    def run(self, scene: Optional[Scene] = None) -> None:
        """Execute the application.

        :param scene.Scene|None scene: scene to start the execution from
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
            await self.mainloop()
        finally:
            pygame.display.quit()
            pygame.mixer.quit()
            self.running = False

    async def mainloop(self) -> None:
        """Run the main loop of Pygame Zero."""
        clock = pygame.time.Clock()
        fps_calc = FPSCalc()

        fps = 0.0
        # self.need_redraw = True
        while True:
            self._screen.clear()

            dt = clock.tick(self.update_rate) / 1000

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

                self.handle_event(event)

            global_clock.tick(dt)
            fps_calc.push(1.0 / dt)
            if fps_calc.counter == 100:
                fps = fps_calc.aver()
                print(f"fps {fps}")

            self.update(dt)

            # screen_change = self.reinit_screen()
            # if screen_change or update or self._clock.fired or self.need_redraw:
            self.draw()

            self._screen.draw.text(f"FPS: {fps}", pos=(0, 0))

            pygame.display.update()
            # self.need_redraw = False
