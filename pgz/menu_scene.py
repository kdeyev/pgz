from typing import Optional

import pygame
import pygame_menu
from pgzero.screen import Screen

from .scene import Scene


class MenuScene(Scene):
    def __init__(self, menu: Optional[pygame_menu.Menu] = None):
        super().__init__()
        self.menu = menu
        if not self.menu:
            self.menu = pygame_menu.Menu(300, 400, "Welcome", theme=pygame_menu.themes.THEME_BLUE)

        # self.menu.add_text_input("Name :", default="John Doe")
        # # self.menu.add_selector('Difficulty :', [('Hard', 1), ('Easy', 2)], onchange=set_difficulty)
        # self.menu.add_button("Play", self.start_the_game)
        # self.menu.add_button("Quit", pygame_menu.events.EXIT)

    @property
    def menu(self) -> pygame_menu.Menu:
        return self._menu

    @menu.setter
    def menu(self, menu: pygame_menu.Menu) -> None:
        self._menu = menu

    def draw(self, surface: Screen) -> None:
        # TODO: may be need to remove disable_loop
        self.menu.mainloop(surface, disable_loop=True)

    def on_exit(self, next_scene: Optional[Scene]) -> None:
        self.menu.disable()

    def handle_event(self, event: pygame.event.Event) -> None:
        self.menu.update([event])
