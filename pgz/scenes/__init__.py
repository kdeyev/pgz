"""
pgz provides an implementation of a few tipical scene classes subclassed from the `pgz.Scene`.

- `pgz.MenuScene` - implements game menu rendering as a pgz.Scene subclass
- `pgz.ActorScene` - implements the basic actors managements, updates, rendering logic and actors collision detection.
- `pgz.MapScene` - extends pgz.ActorScene for games based on the tiled maps. It also implements the tiles collision detection.
- `pgz.RemoteSceneClient` - allows to render the view of remote pgz.MapScene or pgz.ActorScene using WebSocket connection. It might be useful handy for building of a multiplayer game
"""


from .actor_scene import ActorScene  # noqa
from .map_scene import MapScene  # noqa
from .menu_scene import MenuScene  # noqa
