# pgz

pgz aim to make development of advanced [pygame](https://www.pygame.org/) games easier.
pgz uses pgzero as infrastructure intensively, but makes the experience more object oriented.

## Features
- More pytonic infrastructure: pgz utilies a lot of features from [pgzero](https://github.com/lordmauve/pgzero)
- Multi-scene games: The idea and some code was taken from [EzPyGame](https://github.com/Mahi/EzPyGame)
- Maps, collision detection and maps scrolling: the implementation is based on [pyscroll](https://github.com/bitcraft/pyscroll)
- Scenes for rendering Menu based [pygame-menu](https://github.com/ppizarror/pygame-menu)
- Multi-player game over network: based on simple RPC over WebSockets

## Installation

not yet


## Quick start



### Application

The application and scenes idea was from the  [EzPyGame](https://github.com/Mahi/EzPyGame).

pgz application can be started using the code snippet:
```
if __name__ == "__main__":

    app = pgz.Application(
        title="pgz Standalone Demo",
        resolution=(1280, 720),
        update_rate=60,
    )

    try:
        scene = ....
        app.run(scene)

    except Exception:
        # pygame.quit()
        raise
```

### Scene
In the snippet above scene object instantiation ```scene = ....``` was skipped.

The application and scenes idea was from the  [EzPyGame](https://github.com/Mahi/EzPyGame).


Create scenes by subclassing pgz.Scene and overriding any of the following methods:
- handle_event(self, event)
- draw(self, screen)
- update(self, dt)
- on_enter(self, previous_scene)
- on_exit(self, next_scene)

Scenes can be switched by using the Application.change_scene(scene) method:
```
class Game(Scene):
    ...

    def on_enter(self, previous_scene):
        self.previous_scene = previous_scene

    def update(self, dt):
        self.player.move(dt)
        if self.player.died():
            self.application.change_scene(self.previous_scene)
```

### Scene types

pgz provides a list of advanced scenes for subclassing:
- pgz.MenuScene: for menu rendering
- pgz.MapScene: for handling the map based scenes
- Multiplayer Scenes: for handling multiplayer game

## Regular scene


## MapScene

### Map loading
The map object loading is done with the map loader (a-la pgzero resource loaders). So for loading a map from "default.tmx" file of the resource directory: 
```
tmx = pgz.maps.default
```
The "mtx" files can be created and modified with wonderful [Tiled](https://www.mapeditor.org/) mps editor.

### Map management and rendering 
The maps loading and usage is backed by [pyscroll](https://github.com/bitcraft/pyscroll)
    
pgz provides pgz.ScrollMap class which covers listed functionality:
- create and manage a pyscroll group
- load a collision layers
- manage sprites added to the map
- allows to detect collisions with loaded collision layers
- render the map and the sprites on top

### Map Scene

```
class Game(pgz.MapScene):
    def __init__(self, map):
        super().__init__(map)

        self.ship = Ship()
        # put the ship in the center of the map
        self.ship.position = self.map.get_center()
        self.ship.x += 600
        self.ship.y += 400

        # add our ship to the group
        self.add_actor(self.ship, central_actor=True)

    def update(self, dt):
        """Tasks that occur over time should be handled here"""
        self.map.update(dt)

        if self.map.collide(self.ship):
            self.ship.move_back(dt)

    def on_mouse_move(self, pos):
        angle = self.ship.angle_to(pos) + 90
        self.ship.angle = angle

    def boom(self):
        print("boom")

    def on_mouse_down(self, pos, button):
        pgz.sounds.arrr.play()

        ball = CannonBall(self.ship.pos, pos, self.remove_actor)
        self.add_actor(ball)

    def on_key_down(self, key):
        if key == pygame.K_EQUALS:
            self.map.change_zoom(0.25)
        elif key == pygame.K_MINUS:
            self.map.change_zoom(-0.25)

    def handle_event(self, event):
        """Handle pygame input events"""

        # this will be handled if the window is resized
        if event.type == pygame.VIDEORESIZE:
            self.map.set_size((event.w, event.h))
```

### Maps usage

The maps loading and usage is backed by [PyTMX](https://github.com/bitcraft/PyTMX)

```
tmx = pgz.maps.default
map = pgz.ScrollMap(app.resolution, tmx, ["Islands"])
```

## Demo 

![Alt Text](img/demo.gif)