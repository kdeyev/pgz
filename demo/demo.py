from typing import Optional, Tuple

from my_game import GameScene

import pgz


class Menu(pgz.MenuScene):
    def __init__(self):
        super().__init__()
        import pygame_menu

        self.menu = pygame_menu.Menu(300, 400, "Welcome", theme=pygame_menu.themes.THEME_BLUE)

        self.menu.add_text_input("Name :", default="John Doe")
        # self.menu.add_selector('Difficulty :', [('Hard', 1), ('Easy', 2)], onchange=set_difficulty)
        self.menu.add_button("Play", self.start_the_game)
        self.menu.add_button("Quit", pygame_menu.events.EXIT)

    def start_the_game(self):
        scene = GameScene()
        tmx = pgz.maps.default
        map = pgz.ScrollMap(app.resolution, tmx, ["Islands"])
        scene.set_map(map)
        self.change_scene(scene)


if __name__ == "__main__":

    app = pgz.Application(
        title="pgz Standalone Demo",
        resolution=(1280, 720),
        update_rate=60,
    )

    try:
        menu = Menu()
        app.run(menu)

    except Exception:
        # pygame.quit()
        raise
