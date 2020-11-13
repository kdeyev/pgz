from typing import Optional

import pygame_menu
from my_pirate_game import GameScene

import pgz


class ServerScene(pgz.Scene):
    def __init__(self, port):
        super().__init__()
        self.port = port

    def on_enter(self, previous_scene):
        super().on_enter(previous_scene=previous_scene)

        tmx = pgz.maps.default
        map = pgz.ScrollMap((1280, 720), tmx, ["Islands"])

        # Build and start game server
        self.server = pgz.MultiplayerSceneServer(map, GameScene)
        self.server.start_server(port=self.port)

    def on_exit(self, next_scene: Optional[pgz.Scene]):
        self.server.stop_server()
        self.server = None

    def update(self, dt):
        super().update(dt)
        if self.server:
            self.server.update(dt)


class Menu(pgz.MenuScene):
    def __init__(
        self,
    ):
        super().__init__()

        self.server = None

        self.menu = pygame_menu.Menu(300, 400, "Server", theme=pygame_menu.themes.THEME_BLUE)
        self.build_menu()

    def start_the_game(self):
        data = self.menu.get_input_data()
        port = data["port"]

        game = ServerScene(port)
        self.change_scene(game)

    def build_menu(self):
        self.menu.clear()
        if not self.server:
            self.port_widget = self.menu.add_text_input("Port :", textinput_id="port", default="8765", valid_chars=[str(i) for i in range(9)])
            self.menu.add_button("Start", self.start_the_game)
        else:
            self.menu.add_button("Stop", self.stop_the_game)

        self.menu.add_button("Quit", pygame_menu.events.EXIT)


if __name__ == "__main__":
    app = pgz.Application(
        title="pgz Server Demo",
        resolution=(1280, 720),
        update_rate=60,
    )

    try:

        menu = Menu()
        app.run(menu)

    except Exception:
        # pygame.quit()
        raise
