import asyncio
import json
from email import message
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple

# from re import T
from uuid import uuid4

import nest_asyncio
import pydantic
import pygame
import websockets
from pygame import event

# import jsonrpc_base
from .actor import Actor
from .keyboard import Keyboard
from .scene import EventDispatcher, Scene
from .scenes.map_scene import MapScene
from .screen import Screen
from .utils.collision_detector import CollisionDetector
from .utils.screen_rpc import RPCScreenClient, RPCScreenServer
from .utils.scroll_map import ScrollMap

nest_asyncio.apply()

UUID = str
JSON = Dict[str, Any]


class EventNotification(pydantic.BaseModel):
    event_type: int
    attributes: Dict[str, Any]


class EventsNotification(pydantic.BaseModel):
    events: List[EventNotification]


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


class MultiplayerSceneServer:
    def __init__(self, map: ScrollMap, HeadlessSceneClass: Any):
        super().__init__()

        # The map object will be shared between all the headless scenes
        self._map = map
        self._collision_detector = CollisionDetector()

        self._latest_actors = {}

        # Dict of connected clients
        self._clients: Dict[websockets.WebSocketClientProtocol, Scene] = {}
        self._screens: Dict[websockets.WebSocketClientProtocol, RPCScreenServer] = {}

        # Class of the headless scenes. Server will instantiate a scene object per connected client
        assert issubclass(HeadlessSceneClass, Scene)
        self._HeadlessSceneClass = HeadlessSceneClass

    def update(self, dt: float) -> None:
        self._map.update(dt)
        for scenes in self._clients.values():
            scenes.update(dt)

        # server calls internal redraw
        for ws in self._clients:
            scene = self._clients[ws]
            screen = self._screens[ws]

            # Update screen
            scene.draw(screen)

        actors_changed, actors_state_notification = self._get_actors_state()

        for websocket in self._clients:
            scene = self._clients[websocket]
            screen = self._screens[websocket]

            # Get changes
            screen_changed, data = screen.get_messages()
            if not screen_changed and not actors_changed:
                continue

            state_notification = StateNotification(actors=actors_state_notification)

            if screen_changed:
                # Send to client
                state_notification.screen = data

            asyncio.ensure_future(websocket.send(state_notification.json()))

    def _get_actors_state(self):
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

    async def _recv_handshake(self, websocket: websockets.WebSocketClientProtocol, scene: Scene) -> None:
        massage = await websocket.recv()
        massage = json.loads(massage)
        resolution = massage["resolution"]

        rpc_screen = RPCScreenServer(resolution)
        self._screens[websocket] = rpc_screen

        scene.set_client_data(massage["client_data"])

    async def _send_handshake(self, websocket: websockets.WebSocketClientProtocol, scene: Scene) -> None:

        actors: List[Actor] = []
        for sc in self._clients.values():
            actors += sc.get_actors()

        actors_states = {actor.uuid: actor.serialize_state() for actor in actors}

        rpc_screen = self._screens[websocket]

        massage = {"uuid": scene.scene_uuid, "actors_states": actors_states, "screen_state": rpc_screen.get_messages()}
        await websocket.send(json.dumps(massage))

    async def _register_client(self, websocket: websockets.WebSocketClientProtocol) -> None:
        # Create a headless scene
        scene = self._HeadlessSceneClass()
        # Create init the scene
        scene.set_map(self._map)
        scene.set_collision_detector(self._collision_detector)
        scene.block_update = True
        scene.block_draw = True
        scene.accumulate_changes = True

        await self._recv_handshake(websocket, scene)
        await self._send_handshake(websocket, scene)

        self._clients[websocket] = scene
        scene.on_enter(None)

    async def _unregister_client(self, websocket: websockets.WebSocketClientProtocol) -> None:
        scene = self._clients[websocket]

        # First of all remove dead client
        del self._clients[websocket]
        del self._screens[websocket]

        scene.on_exit(None)
        scene.remove_actors()

    def _handle_client_message(self, websocket: websockets.WebSocketClientProtocol, message: str) -> None:
        try:
            scene = self._clients[websocket]
            events_notification = EventsNotification.parse_raw(message)
            for event in events_notification.events:
                scene.dispatch_event(pygame.event.Event(event.event_type, **event.attributes))
        except Exception as e:
            print(f"_handle_client_message: {e}")

    async def _serve_client(self, websocket: websockets.WebSocketClientProtocol, path: str) -> None:
        # register(websocket) sends user_event() to websocket
        await self._register_client(websocket)
        try:
            async for message in websocket:
                try:
                    self._handle_client_message(websocket, message)
                except Exception as e:
                    print(f"_serve_client: {e}")
        finally:
            await self._unregister_client(websocket)

    def start_server(self, host: str = "localhost", port: int = 8765) -> None:
        self._server_task = asyncio.ensure_future(websockets.serve(self._serve_client, host, port))  # type: ignore

    def stop_server(self) -> None:
        self._server_task.cancel()


class RemoteScene(MapScene):
    def __init__(self, map: ScrollMap, server_url: str, client_data: JSON = {}) -> None:
        super().__init__(map)

        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.server_url = server_url
        self._event_notification_queue: List[EventNotification] = []
        self._screen_client = RPCScreenClient()
        self._client_data = client_data

    def on_exit(self, next_scene: Optional[Scene]) -> None:
        super().on_exit(next_scene)

        if self._websocket:
            asyncio.get_event_loop().run_until_complete(self._websocket.close())
            self._websocket = None

    def on_enter(self, previous_scene: Optional[Scene]) -> None:
        super().on_enter(previous_scene)

        asyncio.get_event_loop().run_until_complete(self.connect_to_server())
        if not self._websocket:
            raise Exception("Cannot connect")

    def update(self, dt: float) -> None:
        asyncio.ensure_future(self._flush_messages())
        super().update(dt)

    def draw(self, screen: Screen) -> None:
        super().draw(screen)
        self._screen_client.draw(screen)
        screen.draw.text(self.server_url, pos=(300, 0))

    async def _flush_messages(self) -> None:
        if self._websocket and len(self._event_notification_queue):
            # create one json array
            events_notification = EventsNotification(events=self._event_notification_queue)
            self._event_notification_queue = []
            # send message
            await self._websocket.send(events_notification.json())

    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)

        if not self._websocket:
            # not connected yet
            return

        try:
            event_notification = EventNotification(event_type=event.type, attributes=event.__dict__)
            self._event_notification_queue.append(event_notification)
        except Exception as e:
            print(f"handle_event: {e}")
            return

    async def connect_to_server(self, attempts: int = 10) -> bool:
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
        message: str
        async for message in self._websocket:  # type: ignore
            try:
                state_notification = StateNotification.parse_raw(message)
                uuid: str
                added_actor: AddedActor
                for uuid, added_actor in state_notification.actors.added.items():
                    self.add_actor_on_client(uuid, added_actor.scene_uuid, added_actor.image, added_actor.is_central)

                acrtor_state: Dict[str, Any]
                for uuid, acrtor_state in state_notification.actors.modified.items():
                    self.on_actor_prop_change(uuid, acrtor_state)

                for uuid in state_notification.actors.removed:
                    self.remove_actor_on_client(uuid)

                if state_notification.screen:
                    self.on_screen_redraw(state_notification.screen)

            except Exception as e:
                print(f"_handle_messages: {e}")

    def add_actor_on_client(self, uuid: UUID, scene_uuid: UUID, image: str, central_actor: bool) -> None:
        actor = Actor(image, uuid=uuid)

        if scene_uuid != self.scene_uuid:
            # Foreign actor cannot be central
            central_actor = False

        self.add_actor(actor, central_actor)

    def remove_actor_on_client(self, uuid: UUID) -> None:
        actor: Actor = self.get_actor(uuid)
        self.remove_actor(actor)

    def on_actor_prop_change(self, uuid: UUID, props: Dict[str, Any]) -> None:
        actor = self.get_actor(uuid)
        for prop, value in props.items():
            actor.__setattr__(prop, value)

    def on_screen_redraw(self, data: List[JSON]) -> None:
        self._screen_client.set_messages(data)
