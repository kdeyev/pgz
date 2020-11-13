"""
pgz uses the `pgzero.loaders` module implementation for the source managemens.
More inforamation can be found [here](https://pygame-zero.readthedocs.io/en/stable/builtins.html#resource-loading)

The extension was provided by pgz is the `MapLoader` resource loader, which loads TMX tiled maps in the same manner as all other resources are loaded

Examples:

The example of default.tmx file loading is shown below:
```
tmx = pgz.maps.default
```
"""


from pgzero.loaders import ResourceLoader, fonts, images, set_root, sounds  # noqa
from pytmx import TiledMap
from pytmx.util_pygame import load_pygame


class MapLoader(ResourceLoader):
    EXTNS = ["tmx"]
    TYPE = "map"

    def _load(self, path: str) -> TiledMap:

        return load_pygame(path)


maps = MapLoader("maps")

set_resource_root = set_root
