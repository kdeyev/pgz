import pygame_menu

import pgz

pgz.set_resource_root("demo/resources")


class Menu(pgz.MenuScene):
    def __init__(self):
        super().__init__()

        self.menu = pygame_menu.Menu(300, 400, "Welcome", theme=pygame_menu.themes.THEME_BLUE)

        self.menu.add_text_input("Server :", textinput_id="server_url", default="ws://localhost:8765")
        self.menu.add_text_input("Name :", textinput_id="name", default="John Doe")
        # self.menu.add_selector('Difficulty :', [('Hard', 1), ('Easy', 2)], onchange=set_difficulty)
        self.menu.add_button("Connect", self.start_the_game)
        self.menu.add_button("Quit", pygame_menu.events.EXIT)

    def start_the_game(self):

        data = self.menu.get_input_data()
        server_url = data["server_url"]

        tmx = pgz.maps.default
        map = pgz.ScrollMap(app.resolution, tmx, ["Islands"])
        game = pgz.RemoteSceneClient(map, server_url, client_data={"name": data["name"]})
        self.change_scene(game)


if __name__ == "__main__":
    app = pgz.Application(
        title="pgz Client Demo",
        resolution=(1280, 720),
        update_rate=60,
    )

    try:
        menu = Menu()
        app.run(menu)

    except Exception:
        # pygame.quit()
        raise
