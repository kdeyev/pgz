from typing import Optional

import pygame
import pygame_menu

from ..scene import Scene
from ..screen import Screen


class MenuScene(Scene):
    """
    Base class for a scenes showing menu.

    MenuScene uses `pygame_menu.Menu` internally, for the additional information follow the link [pygame-menu](https://github.com/ppizarror/pygame-menu).

    Examples:
    ```
    class Menu(pgz.MenuScene):
        def __init__(self):
            super().__init__()
            import pygame_menu

            self.menu = pygame_menu.Menu(300, 400, "Welcome", theme=pygame_menu.themes.THEME_BLUE)

            self.menu.add_text_input("Name :", textinput_id="name", default="John Doe")
            self.menu.add_selector('Difficulty :', [('Hard', 1), ('Easy', 2)], onchange=set_difficulty)
            self.menu.add_button("Play", self.start_the_game)
            self.menu.add_button("Quit", pygame_menu.events.EXIT)

        def start_the_game(self):
            data = self.menu.get_input_data()

            scene = GameScene()
            tmx = pgz.maps.default
            map = pgz.ScrollMap(app.resolution, tmx, ["Islands"])
            scene.set_map(map)
            scene.set_client_data({"name": data["name"]})
            self.change_scene(scene)
    ```
    """

    def __init__(self, menu: Optional[pygame_menu.Menu] = None):
        """Create `MenuScene`

        Receives a menu object as argument or creates its own menu object.

        Args:
            menu (Optional[pygame_menu.Menu], optional): menu object. Defaults to None.
        """
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

    def draw(self, screen: Screen) -> None:
        """
        Overriden rendering method
        Implementation of the update method for the ActorScene.

        The ActorScene implementation renders all the actorts attached to the scene.

        Args:
            screen (Screen): screen to draw the scene on
        """

        # TODO: may be need to remove disable_loop
        self.menu.mainloop(screen.surface, disable_loop=True)

    def on_exit(self, next_scene: Optional[Scene]) -> None:
        """
        Overriden deinitialization method

        Args:
            next_scene (Optional[Scene]): next scene to run
        """
        self.menu.disable()

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Overriden event handling method method

        All of `pygame`'s events are sent here, so filtering
        should be applied manually in the subclass.

        Args:
            event (pygame.event.Event): event to handle
        """
        self.menu.update([event])
