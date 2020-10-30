import uuid

import pygame

import pgz

pgz.set_resource_root("demo/resources")

if __name__ == "__main__":
    app = pgz.Application(
        title="My First EzPyGame Application!",
        resolution=(1280, 720),
        update_rate=60,
    )

    try:
        map = pgz.ScrollMap(app.resolution, "default.tmx", ["Islands"])
        menu = pgz.MultiplayerClient(map)
        app.run(menu)

    except Exception:
        # pygame.quit()
        raise
