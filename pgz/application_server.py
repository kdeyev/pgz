import asyncio
import sys

import pygame
from websockets import server

from .clock import FPSCalc
from .clock import clock as global_clock


class Server:
    def __init__(self, title=None, resolution=None, update_rate=None):
        pygame.init()
        self.update_rate = update_rate
        # self._clock = global_clock

        # Trigger property setters
        self.title = title
        self.resolution = resolution

    @property
    def title(self):
        return pygame.display.get_caption()

    @title.setter
    def title(self, value):
        pygame.display.set_caption(value)

    @property
    def resolution(self):
        return self._screen.get_size()

    @resolution.setter
    def resolution(self, value):
        self._screen = pygame.display.set_mode(value)

    async def update(self, dt):
        if self.server:
            await self.server.update(dt)

    def run(self, server):
        self.server = server
        loop = asyncio.SelectorEventLoop()
        try:
            loop.run_until_complete(self.run_as_coroutine())
        finally:
            loop.close()

    async def run_as_coroutine(self):
        self.running = True
        try:
            await self.mainloop()
        finally:
            pygame.display.quit()
            pygame.mixer.quit()
            self.running = False

    async def mainloop(self):
        clock = pygame.time.Clock()
        fps_calc = FPSCalc(100)

        self.server.start_server()
        while True:
            dt = clock.tick(self.update_rate) / 1000

            # TODO: Use asyncio.sleep() for frame delay if accurate enough
            await asyncio.sleep(0)
            for event in pygame.event.get():

                if event.type == pygame.VIDEORESIZE:
                    self.resolution = (event.w, event.h)

                if event.type == pygame.QUIT:
                    self.change_scene(None)  # Trigger Scene.on_exit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q and event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META):
                        sys.exit(0)

            global_clock.tick(dt)
            fps_calc.push(1.0 / dt)
            if fps_calc.counter == 100:
                print(f"Server fps {fps_calc.aver()}")

            await self.update(dt)
