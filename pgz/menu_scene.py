import pygame_menu

from .scene import Scene


class MenuScene(Scene):
    def __init__(self, menu=None):
        super().__init__()
        self.menu = menu
        if not self.menu:
            self.menu = pygame_menu.Menu(300, 400, "Welcome", theme=pygame_menu.themes.THEME_BLUE)

        # self.menu.add_text_input("Name :", default="John Doe")
        # # self.menu.add_selector('Difficulty :', [('Hard', 1), ('Easy', 2)], onchange=set_difficulty)
        # self.menu.add_button("Play", self.start_the_game)
        # self.menu.add_button("Quit", pygame_menu.events.EXIT)

    @property
    def menu(self):
        return self._menu

    @menu.setter
    def menu(self, menu):
        self._menu = menu

    def draw(self, surface):
        # TODO: may be need to remove disable_loop
        self.menu.mainloop(surface, disable_loop=True)

    def on_exit(self, next_scene):
        self.menu.disable()

    def handle_event(self, event):
        self.menu.update([event])
