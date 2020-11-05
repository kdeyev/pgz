from pgzero.loaders import ResourceLoader, fonts, images, set_root, sounds


class MapLoader(ResourceLoader):
    EXTNS = ["tmx"]
    TYPE = "map"

    def _load(self, path):
        from pytmx.util_pygame import load_pygame

        return load_pygame(path)


maps = MapLoader("maps")
