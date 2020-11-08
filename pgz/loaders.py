from pgzero.loaders import ResourceLoader, fonts, images, set_root, sounds
from pytmx import TiledMap
from pytmx.util_pygame import load_pygame


class MapLoader(ResourceLoader):
    EXTNS = ["tmx"]
    TYPE = "map"

    def _load(self, path: str) -> TiledMap:

        return load_pygame(path)


maps = MapLoader("maps")

set_resource_root = set_root
