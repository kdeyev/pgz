<a name="pgz"></a>
# pgz

<a name="pgz.actor"></a>
# pgz.actor

<a name="pgz.actor_scene"></a>
# pgz.actor\_scene

<a name="pgz.actor_scene.ActorScene"></a>
## ActorScene Objects

```python
class ActorScene(Scene)
```

Scene implementation for management of multiple actors.

Actors also can be added to different collision groups,
which allows easily identify collision of an actor with a specific actor group

<a name="pgz.actor_scene.ActorScene.__init__"></a>
#### \_\_init\_\_

```python
 | __init__() -> None
```

Create an ActorScene object

<a name="pgz.actor_scene.ActorScene.set_collision_detector"></a>
#### set\_collision\_detector

```python
 | set_collision_detector(collision_detector: CollisionDetector)
```

Set external collsinion detector object.

The default collision detector can be use in the most of the cases.
This method in used by multiplayer.

<a name="pgz.actor_scene.ActorScene.add_actor"></a>
#### add\_actor

```python
 | add_actor(actor: Actor, group_name: str = "") -> None
```

Add actor to the scene and add the actor to the collision group.

**Arguments**:

- `actor` _Actor_ - actor to add
- `group_name` _str, optional_ - Collision group name. Defaults to "".

<a name="pgz.actor_scene.ActorScene.remove_actor"></a>
#### remove\_actor

```python
 | remove_actor(actor: Actor) -> None
```

Remove actor from the scene.

Actor also will be removed from the associated collision detector

**Arguments**:

- `actor` _Actor_ - Actor to be removed

<a name="pgz.actor_scene.ActorScene.remove_actors"></a>
#### remove\_actors

```python
 | remove_actors() -> None
```

Remove all actors from the scene and the associated collision detector

<a name="pgz.actor_scene.ActorScene.get_actor"></a>
#### get\_actor

```python
 | get_actor(uuid: str) -> Actor
```

Get actor object by its UUID

**Arguments**:

- `uuid` _str_ - UUID of the actor to be retrieved
  

**Returns**:

- `Actor` - Actor associated with the UUID

<a name="pgz.actor_scene.ActorScene.get_actors"></a>
#### get\_actors

```python
 | get_actors() -> List[Actor]
```

Get list of actors

**Returns**:

- `List[Actor]` - The list of actors on the scene

<a name="pgz.actor_scene.ActorScene.collide_group"></a>
#### collide\_group

```python
 | collide_group(actor: Actor, group_name: str = "") -> Optional[Actor]
```

Detect collision of a ginen actor with the actors in requested collsion group.

**Arguments**:

- `actor` _Actor_ - actor to detect collisions with
- `group_name` _str, optional_ - Collision group name. Defaults to "".
  

**Returns**:

- `Optional[Actor]` - A collins actor in the specified collision group

<a name="pgz.actor_scene.ActorScene.draw"></a>
#### draw

```python
 | draw(surface: Screen) -> None
```

Overriden rendering method
Implementation of the update method for the ActorScene.

The ActorScene implementation renders all the actorts attached to the scene.

:param pgz.Screen screen: screen to draw the scene on

<a name="pgz.actor_scene.ActorScene.update"></a>
#### update

```python
 | update(dt: float) -> None
```

Overriden update method
Implementation of the update method for the ActorScene.

This method updates all the actors attached to the scene.

:param int dt: time in milliseconds since the last update

<a name="pgz.application"></a>
# pgz.application

<a name="pgz.application.Application"></a>
## Application Objects

```python
class Application()
```

The idea and the original code was taken from EzPyGame:
https://github.com/Mahi/EzPyGame

A simple wrapper around :mod:`pygame` for running games easily.

Also makes scene management seamless together with
the :class:`.Scene` class.

:param str|None title: title to display in the window's title bar
:param tuple[int,int]|None resolution: resolution of the game window
:param int|None update_rate: how many times per second to update

If any parameters are left to ``None``, these settings must be
defined either manually through ``application.<setting> = value``
or via :class:`.Scene`'s class variable settings.

Example usage:

.. code-block:: python

class Menu(pgz.Scene):
...

class Game(pgz.Scene):
...

app = pgz.Application(
title='My First Application',
resolution=(1280, 720),
update_rate=60,
)
main_menu = Menu()
app.run(main_menu)

<a name="pgz.application.Application.active_scene"></a>
#### active\_scene

```python
 | @property
 | active_scene() -> Optional[Scene]
```

The currently active scene. Can be ``None``.

<a name="pgz.application.Application.change_scene"></a>
#### change\_scene

```python
 | change_scene(scene: Optional[Scene]) -> None
```

Change the currently active scene.

This will invoke :meth:`.Scene.on_exit` and
:meth:`.Scene.on_enter` methods on the switching scenes.

If ``None`` is provided, the application's execution will end.

:param Scene|None scene: the scene to change into

<a name="pgz.application.Application.run"></a>
#### run

```python
 | run(scene: Optional[Scene] = None) -> None
```

Execute the application.

:param scene.Scene|None scene: scene to start the execution from

<a name="pgz.application.Application.mainloop"></a>
#### mainloop

```python
 | async mainloop() -> None
```

Run the main loop of Pygame Zero.

<a name="pgz.clock"></a>
# pgz.clock

<a name="pgz.collision_detector"></a>
# pgz.collision\_detector

<a name="pgz.event_dispatcher"></a>
# pgz.event\_dispatcher

<a name="pgz.event_dispatcher.EventDispatcher"></a>
## EventDispatcher Objects

```python
class EventDispatcher()
```

Adapt a pgzero game's raw handler function to take a Pygame Event.

Returns a one-argument function of the form ``handler(event)``.
This will ensure that the correct arguments are passed to the raw
handler based on its argument spec.

The wrapped handler will also map certain parameter values using
callables from EVENT_PARAM_MAPPERS; this ensures that the value of
'button' inside the handler is a real instance of constants.mouse,
which means (among other things) that it will print as a symbolic value
rather than a naive integer.

<a name="pgz.event_dispatcher.EventDispatcher.handle_event"></a>
#### handle\_event

```python
 | handle_event(event: pygame.event.Event) -> None
```

Override me

<a name="pgz.fps_calc"></a>
# pgz.fps\_calc

<a name="pgz.keyboard"></a>
# pgz.keyboard

<a name="pgz.keyboard.Keyboard"></a>
## Keyboard Objects

```python
class Keyboard()
```

The current state of the keyboard.

Each attribute represents a key. For example, ::

    keyboard.a

is True if the 'A' key is depressed, and False otherwise.

<a name="pgz.loaders"></a>
# pgz.loaders

<a name="pgz.map_scene"></a>
# pgz.map\_scene

<a name="pgz.map_scene.MapScene"></a>
## MapScene Objects

```python
class MapScene(ActorScene)
```

Scene implementation for Tiled map management.

Extends functionality ActorScene, but in case of MapScene actors are placed on a map.
The implementation is based on [pyscroll](https://github.com/bitcraft/pyscroll).
A tiled map can be created and modified with wonderful [Tiled](https://www.mapeditor.org/) maps editor.

The maps loading and usage is backed by [PyTMX](https://github.com/bitcraft/PyTMX)

Actors also can be added to different collision groups,
which allows easily identify collision of an actor with a specific actor group

<a name="pgz.map_scene.MapScene.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(map: Optional[ScrollMap] = None)
```

Create a MapScene object

The map object loading is done with the map loader (a-la pgzero resource loaders). So for loading a map from "default.tmx" file of the resource directory:

```
tmx = pgz.maps.default
map = pgz.ScrollMap(app.resolution, tmx, ["Islands"])
```

**Arguments**:

- `map` _Optional[ScrollMap], optional_ - Loaded map object. Defaults to None.

<a name="pgz.map_scene.MapScene.map"></a>
#### map

```python
 | @property
 | map() -> ScrollMap
```

Get map object

**Returns**:

- `ScrollMap` - the map object used by the scene

<a name="pgz.map_scene.MapScene.set_map"></a>
#### set\_map

```python
 | set_map(map)
```

Set map object

**Arguments**:

- `map` _[type]_ - map object to set

<a name="pgz.map_scene.MapScene.dispatch_event"></a>
#### dispatch\_event

```python
 | dispatch_event(event: pygame.event.Event) -> None
```

Overriden events dispatch method
Used for mouse cursor position transformation into map "world coordinates"

**Arguments**:

- `event` _pygame.event.Event_ - pygame Event object

<a name="pgz.map_scene.MapScene.update"></a>
#### update

```python
 | update(dt: float) -> None
```

Overriden update method
Implementation of the update method for the MapScene.

This method updates all the actors attached to the scene.

**Arguments**:

- `dt` _float_ - time in milliseconds since the last update

<a name="pgz.map_scene.MapScene.draw"></a>
#### draw

```python
 | draw(screen: Screen) -> None
```

Overriden rendering method
Implementation of the update method for the MapScene.

The ActorScene implementation renders all the actorts attached to the scene.

**Arguments**:

- `screen` _Screen_ - screen to draw the scene on

<a name="pgz.map_scene.MapScene.add_actor"></a>
#### add\_actor

```python
 | add_actor(actor: Actor, central_actor: bool = False, group_name: str = "") -> None
```

Overriden add_actor method
Implementation of the add_actor method for the MapScene.

The ActorScene implementation renders all the actorts attached to the scene.

**Arguments**:

- `actor` _Actor_ - actor to add
- `central_actor` _bool, optional_ - Sets the actor to be central actor for the scene. The map view will be centered on the actor. Defaults to False.
- `group_name` _str, optional_ - Collision group name. Defaults to "".

<a name="pgz.map_scene.MapScene.remove_actor"></a>
#### remove\_actor

```python
 | remove_actor(actor: Actor) -> None
```

Overriden remove_actor method
Implementation of the remove_actor method for the MapScene.

**Arguments**:

- `actor` _Actor_ - actor to be removed

<a name="pgz.map_scene.MapScene.handle_event"></a>
#### handle\_event

```python
 | handle_event(event: pygame.event.Event) -> None
```

Overriden event handler
Implementation of the event handler method for the MapScene.

**Arguments**:

- `event` _pygame.event.Event_ - pygame event object

<a name="pgz.map_scene.MapScene.collide_map"></a>
#### collide\_map

```python
 | collide_map(actor: Actor) -> bool
```

Detect collision with tiles in the map object used by the scene

**Arguments**:

- `actor` _Actor_ - actor for collision detection
  

**Returns**:

- `bool` - True if the collision with map tiles is detected

<a name="pgz.menu_scene"></a>
# pgz.menu\_scene

<a name="pgz.multiplayer_scene"></a>
# pgz.multiplayer\_scene

<a name="pgz.rect"></a>
# pgz.rect

<a name="pgz.rpc"></a>
# pgz.rpc

<a name="pgz.scene"></a>
# pgz.scene

<a name="pgz.scene.Scene"></a>
## Scene Objects

```python
class Scene(EventDispatcher)
```

The idea and the original code was taken from EzPyGame:
https://github.com/Mahi/EzPyGame


An isolated scene which can be ran by an application.

Create your own scene by subclassing and overriding any methods.
The hosting :class:`.Application` instance is accessible
through the :attr:`application` property.

Example usage with two scenes interacting:

.. code-block:: python

    class Menu(Scene):

        def __init__(self):
            self.font = pygame.font.Font(...)

        def on_enter(self, previous_scene):
            self.application.title = 'Main Menu'
            self.application.resolution = (640, 480)
            self.application.update_rate = 30

        def draw(self, screen):
            pygame.draw.rect(...)
            text = self.font.render(...)
            screen.blit(text, ...)

        def handle_event(self, event):
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    game_size = self._get_game_size(event.pos)
                    self.change_scene(Game(game_size))

        def _get_game_size(self, mouse_pos_upon_click):
            ...


    class Game(ezpygame.Scene):
        title = 'The Game!'
        resolution = (1280, 720)
        update_rate = 60

        def __init__(self, size):
            super().__init__()
            self.size = size
            self.player = ...
            ...

        def on_enter(self, previous_scene):
            super().on_enter(previous_scene)
            self.previous_scene = previous_scene

        def draw(self, screen):
            self.player.draw(screen)
            for enemy in self.enemies:
                ...

        def update(self, dt):
            self.player.move(dt)
            ...
            if self.player.is_dead():
                self.application.change_scene(self.previous_scene)
            elif self.player_won():
                self.application.change_scene(...)

        def handle_event(self, event):
            ...  # Player movement etc.

The above two classes use different approaches for changing
the application's settings when the scene is entered:

1. Manually set them in :meth:`on_enter`, as seen in ``Menu``
2. Use class variables, as I did with ``Game``

When using class variables (2), you can leave out any setting
(defaults to ``None``) to not override that particular setting.
If you override :meth:`on_enter` in the subclass, you must call
``super().on_enter(previous_scene)`` to use the class variables.

These settings can further be overridden in individual instances:

.. code-block:: python

    my_scene0 = MyScene()
    my_scene0.resolution = (1280, 720)
    my_scene1 = MyScene(title='My Second Awesome Scene')


Shotcuts for simpler event handling:

def on_mouse_up(self, pos, button):
    # Override this for easier events handling.
    pass

def on_mouse_down(self, pos, button):
    # Override this for easier events handling.
    pass

def on_mouse_move(self, pos):
    # Override this for easier events handling.
    pass

def on_key_down(self, key):
    # Override this for easier events handling.
    pass

def on_key_up(self, key):
    # Override this for easier events handling.
    pass

<a name="pgz.scene.Scene.scene_uuid"></a>
#### scene\_uuid

```python
 | @property
 | scene_uuid() -> str
```

Get scene UUID.

<a name="pgz.scene.Scene.client_data"></a>
#### client\_data

```python
 | @property
 | client_data() -> Dict[str, Any]
```

Get data provided by cleint side.

<a name="pgz.scene.Scene.clock"></a>
#### clock

```python
 | @property
 | clock() -> Clock
```

Clock object. Actually returns the global clock object.

<a name="pgz.scene.Scene.keyboard"></a>
#### keyboard

```python
 | @property
 | keyboard() -> Keyboard
```

Clock object. Actually returns the global clock object.

<a name="pgz.scene.Scene.draw"></a>
#### draw

```python
 | draw(screen: Screen) -> None
```

Override this with the scene drawing.

:param pgz.Screen screen: screen to draw the scene on

<a name="pgz.scene.Scene.update"></a>
#### update

```python
 | update(dt: float) -> None
```

Override this with the scene update tick.

:param int dt: time in milliseconds since the last update

<a name="pgz.scene.Scene.handle_event"></a>
#### handle\_event

```python
 | handle_event(event: pygame.event.Event) -> None
```

Override this to handle an event in the scene.

All of :mod:`pygame`'s events are sent here, so filtering
should be applied manually in the subclass.

:param pygame.event.Event event: event to handle

<a name="pgz.scene.Scene.on_enter"></a>
#### on\_enter

```python
 | on_enter(previous_scene: Optional["Scene"]) -> None
```

Override this to initialize upon scene entering.

The :attr:`application` property is initialized at this point,
so you are free to access it through ``self.application``.
Stuff like changing resolution etc. should be done here.

If you override this method and want to use class variables
to change the application's settings, you must call
``super().on_enter(previous_scene)`` in the subclass.

:param Scene|None previous_scene: previous scene to run

<a name="pgz.scene.Scene.on_exit"></a>
#### on\_exit

```python
 | on_exit(next_scene: Optional["Scene"]) -> None
```

Override this to deinitialize upon scene exiting.

The :attr:`application` property is still initialized at this
point. Feel free to do saving, settings reset, etc. here.

:param Scene|None next_scene: next scene to run

<a name="pgz.screen"></a>
# pgz.screen

<a name="pgz.screen_rpc"></a>
# pgz.screen\_rpc

<a name="pgz.screen_rpc.RPCSurfacePainter"></a>
## RPCSurfacePainter Objects

```python
class RPCSurfacePainter()
```

Interface to pygame.draw that is bound to a surface.

<a name="pgz.screen_rpc.RPCSurfacePainter.line"></a>
#### line

```python
 | line(start: Tuple[Any, Any], end: Tuple[Any, Any], color: Any, width: int = 1) -> None
```

Draw a line from start to end.

<a name="pgz.screen_rpc.RPCSurfacePainter.circle"></a>
#### circle

```python
 | circle(pos: Tuple[Any, Any], radius: float, color: Any, width: int = 1) -> None
```

Draw a circle.

<a name="pgz.screen_rpc.RPCSurfacePainter.filled_circle"></a>
#### filled\_circle

```python
 | filled_circle(pos: Tuple[Any, Any], radius: float, color: Any) -> None
```

Draw a filled circle.

<a name="pgz.screen_rpc.RPCSurfacePainter.polygon"></a>
#### polygon

```python
 | polygon(points: List[Tuple[Any, Any]], color: Any) -> None
```

Draw a polygon.

<a name="pgz.screen_rpc.RPCSurfacePainter.filled_polygon"></a>
#### filled\_polygon

```python
 | filled_polygon(points: List[Tuple[Any, Any]], color: Any) -> None
```

Draw a filled polygon.

<a name="pgz.screen_rpc.RPCSurfacePainter.rect"></a>
#### rect

```python
 | rect(rect: ZRect, color: Any, width: int = 1) -> None
```

Draw a rectangle.

<a name="pgz.screen_rpc.RPCSurfacePainter.filled_rect"></a>
#### filled\_rect

```python
 | filled_rect(rect: ZRect, color: Any) -> None
```

Draw a filled rectangle.

<a name="pgz.screen_rpc.RPCSurfacePainter.text"></a>
#### text

```python
 | text(*args: Any, **kwargs: Any) -> None
```

Draw text to the screen.

<a name="pgz.screen_rpc.RPCSurfacePainter.textbox"></a>
#### textbox

```python
 | textbox(*args: Any, **kwargs: Any) -> None
```

Draw text to the screen, wrapped to fit a box

<a name="pgz.screen_rpc.RPCScreenServer"></a>
## RPCScreenServer Objects

```python
class RPCScreenServer()
```

<a name="pgz.screen_rpc.RPCScreenServer.bounds"></a>
#### bounds

```python
 | bounds() -> ZRect
```

Return a Rect representing the bounds of the screen.

<a name="pgz.screen_rpc.RPCScreenServer.clear"></a>
#### clear

```python
 | clear() -> None
```

Clear the screen to black.

<a name="pgz.scroll_map"></a>
# pgz.scroll\_map

<a name="pgz.scroll_map.ScrollMap"></a>
## ScrollMap Objects

```python
class ScrollMap(object)
```

This class provides functionality:
- create and manage a pyscroll group
- load a collision layers
- manage sprites added to the map
- allows to detect collisions with loaded collision layers
- render the map and the sprites on top

<a name="pgz.scroll_map.ScrollMap.update"></a>
#### update

```python
 | update(dt: float) -> None
```

Tasks that occur over time should be handled here

