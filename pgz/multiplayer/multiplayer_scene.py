import asyncio
import datetime
import json
import threading
import time
from email import message
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple

# from re import T
from uuid import uuid4

import nest_asyncio
import pydantic
import pygame
import websockets
from asgiref.sync import async_to_sync
from pygame import event
from websockets import client

from pgz.utils.fps_calc import FPSCalc

# import jsonrpc_base
from ..actor import Actor
from ..keyboard import Keyboard
from ..scene import EventDispatcher, Scene
from ..scenes.map_scene import MapScene
from ..screen import Screen
from ..utils.collision_detector import CollisionDetector
from ..utils.scroll_map import ScrollMap
from .screen_rpc import RPCScreenClient, RPCScreenServer

# from pgz.utils.profiler import profile


nest_asyncio.apply()

UUID = str
JSON = Dict[str, Any]
PROFILE = True


class EventNotification(pydantic.BaseModel):
    event_type: int
    attributes: Dict[str, Any]


class EventsNotification(pydantic.BaseModel):
    events: List[EventNotification]
    time: Optional[datetime.datetime]


class AddedActor(pydantic.BaseModel):
    image: str
    scene_uuid: str
    is_central: bool


class ActorsStateNotification(pydantic.BaseModel):
    added: Dict[str, AddedActor] = {}
    removed: List[str] = []
    modified: Dict[str, Dict[str, Any]] = {}

    def is_empty(self):
        return not self.added and not self.removed and not self.modified


class StateNotification(pydantic.BaseModel):
    actors: ActorsStateNotification
    screen: List[Dict[str, Any]] = []
    time: Optional[datetime.datetime]


class ClientInfo:
    def __init__(self, scene, websocket, screen) -> None:
        self.scene = scene
        self.websocket = websocket
        self.screen = screen
        self.events = asyncio.Queue()


class MultiplayerSceneServer:
    """
    Scene server implementation.

    MultiplayerSceneServer opens a WebSocket server and instantiate a pgz.Scene per connected player(client):
    ```
    tmx = pgz.maps.default
    map = pgz.ScrollMap((1280, 720), tmx, ["Islands"])

    # Build and start game server
    self.server = pgz.MultiplayerSceneServer(map, GameScene)
    self.server.start_server(port=self.port)
    ```

    All the scenes will share the map object and collision detector object. So, the communication between different players scenes is done with collision detection.
    If one scene shoots the cannon ball (by implementing the CannonBall actor and adding its instance to the map):
    ```
    def on_mouse_down(self, pos, button):
        start_point = self.calc_cannon_ball_start_pos(pos)
        if start_point:
            ball = CannonBall(pos=start_point, target=pos)
            self.add_actor(ball, group_name="cannon_balls")
    ```
    Another player(scene) might be harmed by the cannon ball using the collision detection:
    ```
    def update(self, dt):
        super().update(dt)

        cannon_ball = self.collide_group(self.ship, "cannon_balls")
        if cannon_ball:
            # pgz.sounds.arrr.play()
            self.ship.health -= cannon_ball.hit_rate * dt
    ```
    """

    def __init__(self, map: ScrollMap, HeadlessSceneClass: Scene):
        """Create MultiplayerSceneServer instance.

        Args:
            map (ScrollMap): a `pgz.ScrollMap` object. Will be shared across all the scenes in the server
            HeadlessSceneClass (Callable): a scene class. HeadlessSceneClass will be used as a scene object factory.
        """
        super().__init__()

        # The map object will be shared between all the headless scenes
        self._map = map
        # The collision detector object will be shared between all the headless scenes
        self._collision_detector = CollisionDetector()

        self._latest_actors = {}

        # Dict of connected clients
        self._clients: Dict[websockets.WebSocketClientProtocol, ClientInfo] = {}

        # Class of the headless scenes. Server will instantiate a scene object per connected client
        assert issubclass(HeadlessSceneClass, Scene)
        self._HeadlessSceneClass = HeadlessSceneClass

        self._clients_to_add = asyncio.Queue()
        self._clients_to_delete = asyncio.Queue()

        self._notifications_to_send = asyncio.Queue()

        if PROFILE:
            self.processing_calc = FPSCalc()
            self.delivery_calc = FPSCalc()

    # @profile()
    def update(self, dt: float) -> None:
        """Update method similar to the `pgz.scene.Scene.update` method.

        Args:
            dt (float): time in microseconds/1000. since the last update
        """

        try:
            while True:
                client = self._clients_to_delete.get_nowait()
                # First of all remove dead client
                del self._clients[client.websocket]

                client.scene.on_exit(None)
                client.scene.remove_actors()
        except asyncio.QueueEmpty:
            pass

        try:
            while True:
                client = self._clients_to_add.get_nowait()
                self._clients[client.websocket] = client
                # Finally call on_enter of the new scene
                client.scene.on_enter(None)
        except asyncio.QueueEmpty:
            pass

        # Dispatch all the accumulated events
        for client in self._clients.values():
            try:
                while True:
                    event = client.events.get_nowait()
                    client.scene.dispatch_event(event)
            except asyncio.QueueEmpty:
                pass

        # Update all the client scenes
        self._map.update(dt)
        for client in self._clients.values():
            client.scene.update(dt)

        # Server calls internal redraw
        for client in self._clients.values():
            # Update screen
            client.scene.draw(client.screen)

        # Get state of all the actors
        actors_changed, actors_state_notification = self._get_actors_state()

        for websocket, client in self._clients.items():

            # Get changes from the client's screen
            screen_changed, data = client.screen.get_messages()
            if not screen_changed and not actors_changed:
                # Nothing was changed skip notification sending
                continue

            # Create a notification object
            state_notification = StateNotification(actors=actors_state_notification)
            if PROFILE:
                state_notification.time = datetime.datetime.now()

            if screen_changed:
                # Attach the screen update to the notification
                state_notification.screen = data

            self._notifications_to_send.put_nowait((websocket, state_notification))
            # Sent the notification
            # async_to_sync(websocket.send)(state_notification.json())

    # @profile()
    def _get_actors_state(self) -> ActorsStateNotification:
        """Collect the state of all the known actors.

        Returns:
            ActorsStateNotification: the actors state
        """
        actors_state = ActorsStateNotification()
        changed = False
        current_actors = []
        for actor in self._collision_detector.get_actors():
            current_actors.append(actor.uuid)
            if actor.uuid not in self._latest_actors:
                changed = True
                actors_state.added[actor.uuid] = AddedActor(image=actor.image, scene_uuid=actor.scene_uuid, is_central=actor.is_central_actor)
                # "state": actor.serialize_state()

            increment = actor.get_incremental_changes()
            if increment:
                changed = True
                actors_state.modified[actor.uuid] = increment

        for uuid in self._latest_actors:
            if uuid not in current_actors:
                changed = True
                actors_state.removed.append(uuid)
        self._latest_actors = current_actors

        return changed, actors_state

    async def _recv_handshake(self, websocket: websockets.WebSocketClientProtocol, client: ClientInfo) -> None:
        """Receive handshake message from recently connected client.

        Args:
            websocket (websockets.WebSocketClientProtocol): ws client object
            scene (Scene): a scene object associated with the client
        """
        massage = await websocket.recv()
        json_massage = json.loads(massage)
        resolution = json_massage["resolution"]

        # Create screen for the client
        client.screen = RPCScreenServer(resolution)

        client.scene.set_client_data(json_massage["client_data"])

    async def _send_handshake(self, websocket: websockets.WebSocketClientProtocol, client: ClientInfo) -> None:
        """Send handshake method.

        The handshake message will include the current state of the actors attached to the map object

        Args:
            websocket (websockets.WebSocketClientProtocol): ws client object
            scene (Scene): a scene object associated with the client
        """
        actors: List[Actor] = self._collision_detector.get_actors()
        actors_states = {actor.uuid: actor.serialize_state() for actor in actors}

        rpc_screen = client.screen

        massage = {"uuid": client.scene.scene_uuid, "actors_states": actors_states, "screen_state": rpc_screen.get_messages()}
        await websocket.send(json.dumps(massage))

    async def _register_client(self, websocket: websockets.WebSocketClientProtocol) -> None:
        """Register a connected client.

        Create a scene and prepare it for multiplayer game.

        Args:
            websocket (websockets.WebSocketClientProtocol): ws client object
        """
        # Create a headless scene
        scene = self._HeadlessSceneClass()
        # Set a shared map
        scene.set_map(self._map)
        # Set a shared collision detector
        scene.set_collision_detector(self._collision_detector)

        # block `pgz.actor.Actor.update` method for all the actors will be attached to the scene
        scene.block_update = True
        # block `pgz.actor.Actor.draw` method for all the actors will be attached to the scene
        scene.block_draw = True
        # Notify actors to accumulate incremental changes.
        scene.accumulate_changes = True

        client = ClientInfo(scene=scene, websocket=websocket, screen=None)

        await self._recv_handshake(websocket, client)
        await self._send_handshake(websocket, client)

        self._clients_to_add.put_nowait(client)

    async def _unregister_client(self, websocket: websockets.WebSocketClientProtocol) -> None:
        """Unregister a client.

        Usually happens on the client disconnetion.
        Args:
            websocket (websockets.WebSocketClientProtocol): ws client object to unregister
        """
        client = self._clients[websocket]

        self._clients_to_delete.put_nowait(client)

    # @profile()
    def _handle_client_message(self, websocket: websockets.WebSocketClientProtocol, message: str) -> None:
        """Handle a message from a WebSocket client.

        Args:
            websocket (websockets.WebSocketClientProtocol): ws client object sent a message
            message (str): message body
        """
        try:
            client = self._clients[websocket]
            events_notification = EventsNotification.parse_raw(message)

            if PROFILE:
                now = datetime.datetime.now()
                delivery = now - events_notification.time

            for event in events_notification.events:
                # Accumulate events
                client.events.put_nowait(pygame.event.Event(event.event_type, **event.attributes))

            if PROFILE:
                processing = datetime.datetime.now() - now

                self.delivery_calc.push(delivery.microseconds / 1000.0)
                self.processing_calc.push(processing.microseconds / 1000.0)
                if self.delivery_calc.counter == 100:
                    print(f"EventsNotification delivery {self.delivery_calc.aver()} processing {self.processing_calc.aver()}")

        except Exception as e:
            print(f"_handle_client_message: {e}")

    async def _serve_client(self, websocket: websockets.WebSocketClientProtocol, path: str) -> None:
        """Handler funcion for incoming websocket connection.

        Args:
            websocket (websockets.WebSocketClientProtocol): incoming ws client object
            path (str): connection path used by the client
        """

        # Register the client (create a client scene)
        await asyncio.ensure_future(self._register_client(websocket))  # type: ignore
        try:
            async for message in websocket:
                try:
                    self._handle_client_message(websocket, message)
                except Exception as e:
                    print(f"_serve_client: {e}")
        finally:
            await self._unregister_client(websocket)

    async def _send_notifications(self) -> None:
        while True:
            (websocket, notification) = await self._notifications_to_send.get()
            asyncio.ensure_future(websocket.send(notification.json()))

    def start_server(self, host: str = "localhost", port: int = 8765) -> None:
        """Start the scene server.

        Args:
            host (str, optional): host name. Defaults to "localhost".
            port (int, optional): port number for listeting of a incoming WebSocket connections. Defaults to 8765.
        """

        self._server_task = asyncio.ensure_future(websockets.serve(self._serve_client, host, port))  # type: ignore
        asyncio.ensure_future(self._send_notifications())

    def stop_server(self) -> None:
        """Stop the server and disconnect all the clients"""
        self._server_task.cancel()


class RemoteSceneClient(MapScene):
    """
    pgz.RemoteSceneClient allows to communicate with pgz.MultiplayerSceneServer and render the remote scene locally:
    ```
    data = self.menu.get_input_data()
    server_url = data["server_url"]

    tmx = pgz.maps.default
    map = pgz.ScrollMap(app.resolution, tmx, ["Islands"])
    game = pgz.RemoteSceneClient(map, server_url, client_data={"name": data["name"]})
    ```
    Pay attention that client process needs to have access to the same external resources (like map files, images,...) as the game server.

    Pay attention that the `RemoteSceneClient` uses `pgz.RPCScreenClient` instead of `pgz.Screen`.
    """

    def __init__(self, map: ScrollMap, server_url: str, client_data: JSON = {}) -> None:
        """Create a remote scene client object.

        `client_data` will be send to the remote scene object. The common usage - remote scene configuration.
        For example the used select the players avatar image: the image name should be a part of the client_data object.
        So the remote scene will be able to load a correct sprite and the actor's state with other clients.

        Args:
            map (ScrollMap): map object will be used for actors management and rendering
            server_url (str): remote server URL
            client_data (JSON, optional): data will be sent to the remote scene object. Defaults to {}.
        """
        super().__init__(map)

        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.server_url = server_url
        self._event_notification_queue = asyncio.Queue()
        self._screen_client = RPCScreenClient()
        self._client_data = client_data

        if PROFILE:
            self.processing_calc = FPSCalc()
            self.delivery_calc = FPSCalc()
            self.events_count = FPSCalc()

    def on_exit(self, next_scene: Optional[Scene]) -> None:
        """
        Overriden deinitialization method

        Args:
            next_scene (Optional[Scene]): next scene to run
        """
        super().on_exit(next_scene)

        if self._websocket:
            asyncio.get_event_loop().run_until_complete(self._websocket.close())
            self._websocket = None

    def on_enter(self, previous_scene: Optional[Scene]) -> None:
        """
        Overriden initialization method

        Args:
            previous_scene (Optional[Scene]): previous scene was running
        """
        super().on_enter(previous_scene)

        asyncio.get_event_loop().run_until_complete(self.connect_to_server())
        if not self._websocket:
            raise Exception("Cannot connect")

    # @profile()
    def update(self, dt: float) -> None:
        """
        Overriden update method

        Args:
            dt (float): time in microseconds/1000. since the last update
        """
        async_to_sync(self._flush_messages)()
        super().update(dt)

    # @profile()
    def draw(self, screen: Screen) -> None:
        """
        Overriden rendering method

        Args:
            screen (Screen): screen to draw the scene on
        """
        super().draw(screen)
        self._screen_client.draw(screen)
        screen.draw.text(self.server_url, pos=(300, 0))

    async def _flush_messages(self) -> None:
        """Combine all the accumulated event into notification and send to the remote scene."""
        if self._websocket:
            events = []
            last_mouse_mov = None
            try:
                while True:
                    event = self._event_notification_queue.get_nowait()

                    if event.event_type == pygame.MOUSEMOTION:
                        # Mouse events optimization
                        if last_mouse_mov:
                            last_mouse_mov.attributes = event.__dict__
                            continue
                        else:
                            last_mouse_mov = event

                    events.append(event)
            except asyncio.QueueEmpty:
                pass

            if not events:
                return

            # create one json array
            events_notification = EventsNotification(events=events)

            if PROFILE:
                events_notification.time = datetime.datetime.now()
                self.events_count.push(len(events))
                if self.events_count.counter == 100:
                    print(f"Event queue {self.events_count.aver()}")

            # send message
            await self._websocket.send(events_notification.json())

    # @profile()
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Overriden event handler

        Events will be accumulated internally and flushed all together to the remote scene.

        Args:
            event (pygame.event.Event): pygame event object
        """

        super().handle_event(event)

        if not self._websocket:
            # not connected yet
            return

        try:
            event_notification = EventNotification(event_type=event.type, attributes=event.__dict__)
            self._event_notification_queue.put_nowait(event_notification)
        except Exception as e:
            print(f"handle_event: {e}")
            return

    async def connect_to_server(self, attempts: int = 10) -> bool:
        """Connect to the remote scene server.

        Args:
            attempts (int, optional): number of attempts to connect. Defaults to 10.

        Returns:
            bool: True if connected successfully
        """
        websocket: Optional[websockets.WebSocketClientProtocol] = None

        for attempt in range(attempts):
            try:
                websocket = await websockets.connect(self.server_url)
                break
            except OSError as e:
                print(f"handle_event: {e}")
                asyncio.sleep(1)
        if websocket:
            await self._send_handshake(websocket)
            await self._recv_handshake(websocket)
            self._websocket = websocket
            asyncio.ensure_future(self._handle_messages())
            return True
        else:
            return False

    async def _send_handshake(self, websocket: websockets.WebSocketClientProtocol) -> None:
        massage = {"resolution": list(self._application.resolution), "client_data": self._client_data}
        await websocket.send(json.dumps(massage))

    async def _recv_handshake(self, websocket: websockets.WebSocketClientProtocol) -> None:
        data = await websocket.recv()
        massage = json.loads(data)

        self._scene_uuid = massage["uuid"]
        actors_states: Dict[UUID, JSON] = massage["actors_states"]
        uuid: UUID
        state: JSON
        for uuid, state in actors_states.items():
            image = state["image"]
            actor = Actor(image, uuid=uuid)
            for attr, value in state.items():
                setattr(actor, attr, value)

            self.add_actor(actor)

    async def _handle_messages(self) -> None:
        """Handle notifications coming form remote scene."""
        message: str
        async for message in self._websocket:  # type: ignore
            try:
                # Parse the message
                state_notification = StateNotification.parse_raw(message)

                if PROFILE:
                    now = datetime.datetime.now()
                    delivery = now - state_notification.time

                uuid: str
                added_actor: AddedActor
                # Add new actors if required
                for uuid, added_actor in state_notification.actors.added.items():
                    self._add_actor_on_client(uuid, added_actor.scene_uuid, added_actor.image, added_actor.is_central)

                acrtor_state: Dict[str, Any]
                # Modify actors if required
                for uuid, acrtor_state in state_notification.actors.modified.items():
                    self._modify_actor(uuid, acrtor_state)

                # Delete actors if required
                for uuid in state_notification.actors.removed:
                    self._remove_actor_on_client(uuid)

                # Modify screen object if required
                if state_notification.screen:
                    self._modify_screnn(state_notification.screen)

                if PROFILE:
                    processing = datetime.datetime.now() - now

                    self.delivery_calc.push(delivery.microseconds / 1000.0)
                    self.processing_calc.push(processing.microseconds / 1000.0)
                    if self.delivery_calc.counter == 100:
                        print(f"StateNotification delivery {self.delivery_calc.aver()} processing {self.processing_calc.aver()}")
            except Exception as e:
                print(f"_handle_messages: {e}")

    def _add_actor_on_client(self, uuid: UUID, scene_uuid: UUID, image: str, central_actor: bool) -> None:
        """Add actor to the scene.

        Args:
            uuid (UUID): [description]
            scene_uuid (UUID): [description]
            image (str): [description]
            central_actor (bool): [description]
        """
        actor = Actor(image, uuid=uuid)

        if scene_uuid != self.scene_uuid:
            # Foreign actor cannot be central
            central_actor = False

        self.add_actor(actor, central_actor)

    def _remove_actor_on_client(self, uuid: UUID) -> None:
        """Remove an actor from the scene

        Args:
            uuid (UUID): [description]
        """
        actor: Actor = self.get_actor(uuid)
        self.remove_actor(actor)

    def _modify_actor(self, uuid: UUID, props: Dict[str, Any]) -> None:
        """Modify an actor.

        Args:
            uuid (UUID): [description]
            props (Dict[str, Any]): [description]
        """
        actor = self.get_actor(uuid)
        for prop, value in props.items():
            actor.__setattr__(prop, value)

    def _modify_screnn(self, data: List[JSON]) -> None:
        """Modify the screen object

        Args:
            data (List[JSON]): [description]
        """
        self._screen_client.set_messages(data)
