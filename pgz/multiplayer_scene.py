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

from pgz.actor_scene import CollisionDetector

# import jsonrpc_base
from .actor import Actor
from .keyboard import Keyboard
from .map_scene import MapScene
from .scene import EventDispatcher, Scene
from .screen import Screen
from .screen_rpc import RPCScreenClient, RPCScreenServer
from .scroll_map import ScrollMap

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


# class MultiplayerClientHeadlessScene(MapScene):
#     def __init__(self) -> None:
#         super().__init__()

#     # def init_scene_(self, map: ScrollMap, collision_detector: CollisionDetector) -> None:
#     #     """
#     #     Server API:
#     #     Scene initialization by the server
#     #     """
#     #     self.set_map(map)
#     #     self.set_collision_detector(collision_detector)
#     #     # self._broadcast_message = _broadcast_message

#     # def handle_message_(self, message: JSON) -> None:
#     #     """
#     #     Server API:
#     #     Handle event message coming from the client
#     #     """
#     #     try:
#     #         self._rpc.dispatch(message)
#     #     except Exception as e:
#     #         print(f"handle_message_: {e}")

#     # def _send_message(self, json_message: JSON) -> None:
#     #     """
#     #     Send message to the client fo the scene.
#     #     """
#     #     self._message_queue.put_nowait(json_message)

#     # def _broadcast_property_change(self, uuid: str, prop: str, value: Any) -> None:
#     #     """
#     #     Send message about actor's property change.
#     #     """
#     #     if self._broadcast_message:
#     #         json_message = serialize_json_message("on_actor_prop_change", uuid, prop, value)
#     #         self._broadcast_message(json_message)

#     def draw(self, screen: Screen) -> None:
#         """Override this with the scene drawing.

#         :param pygame.Surface screen: screen to draw the scene on
#         """

#         # DO NOT Call super().draw(screen)

#     def on_enter(self, previous_scene: Optional[Scene] = None) -> None:
#         """Override this to initialize upon scene entering.

#         The :attr:`application` property is initialized at this point,
#         so you are free to access it through ``self.application``.
#         Stuff like changing resolution etc. should be done here.

#         If you override this method and want to use class variables
#         to change the application's settings, you must call
#         ``super().on_enter(previous_scene)`` in the subclass.

#         :param Scene|None previous_scene: previous scene to run
#         """
#         super().on_enter(previous_scene)

#     def on_exit(self, next_scene: Optional[Scene] = None) -> None:
#         """Override this to deinitialize upon scene exiting.

#         The :attr:`application` property is still initialized at this
#         point. Feel free to do saving, settings reset, etc. here.

#         :param Scene|None next_scene: next scene to run
#         """
#         super().on_exit(next_scene)

#     def handle_event(self, event: pygame.event.Event) -> None:
#         """Override this to handle an event in the scene.

#         All of :mod:`pygame`'s events are sent here, so filtering
#         should be applied manually in the subclass.

#         :param pygame.event.Event event: event to handle
#         """
#         super().handle_event(event)

#     def update(self, dt: float) -> None:
#         """Override this with the scene update tick.

#         :param int dt: time in milliseconds since the last update
#         """
#         # DO NOT call super().update(dt)

#     def add_actor(self, actor: Actor, central_actor: bool = False, group_name: str = "") -> None:
#         """
#         Add actor to the scene and send notifications to the  clients.

#         If central_actor is True, client's camera will track the actor position. You can have only one central actor on the scene.
#         """
#         super().add_actor(actor, central_actor=central_actor, group_name=group_name)
#         # actor._on_prop_change = self._broadcast_property_change

#         # if self._broadcast_message:
#         #     json_message = serialize_json_message("add_actor_on_client", actor.uuid, self.scene_uuid, actor.image, central_actor)
#         #     self._broadcast_message(json_message)

#     def remove_actor(self, actor: Actor) -> None:
#         """
#         Remore actor from the scene and send notifications to the  clients.
#         """

#         super().remove_actor(actor)

#         # uuid = actor.uuid
#         # if self._broadcast_message:
#         #     json_message = serialize_json_message("remove_actor_on_client", uuid)
#         #     self._broadcast_message(json_message)


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
                # json_message = serialize_json_message("on_screen_redraw", data)
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

    # def _broadcast_message(self, json_message: JSON) -> None:
    #     for scene in self._clients.values():
    #         scene._message_queue.put_nowait(json_message)

    # async def _flush_messages(self) -> None:
    #     if self._clients:  # asyncio.wait doesn't accept an empty list
    #         try:
    #             send_events = []
    #             for websocket, scene in self._clients.items():
    #                 # There are messages in the queue
    #                 if not scene._message_queue.empty():
    #                     # create one json array
    #                     message = serialize_json_array_from_queue(scene._message_queue)
    #                     # send broadcast
    #                     send_event = websocket.send(message)
    #                     send_events.append(send_event)

    #             # wait for all events
    #             if send_events:
    #                 await asyncio.wait(send_events)
    #         except Exception as e:
    #             print(f"MultiplayerSceneServer._broadcast: {e}")

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

        # scene.start_update_loop(update_rate=self.update_rate)

        self._clients[websocket] = scene
        scene.on_enter(None)

    async def _unregister_client(self, websocket: websockets.WebSocketClientProtocol) -> None:
        scene = self._clients[websocket]

        # First of all remove dead client
        del self._clients[websocket]
        del self._screens[websocket]

        scene.on_exit(None)
        # scene.stop_update_loop()
        scene.remove_actors()
        # await notify_users()

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
        # self._flush_messages_task = asyncio.ensure_future(self._flush_messages_loop())

    def stop_server(self) -> None:
        self._server_task.cancel()
        # self._flush_messages_task.cancel()

    # async def _flush_messages_loop(self):
    #     current_time = time.time()
    #     while True:
    #         last_time, current_time = current_time, time.time()
    #         dt = 1 / self.update_rate - (current_time - last_time)
    #         await asyncio.sleep(dt)  # tick
    #         await self._flush_messages()


class MultiplayerClient(MapScene):
    def __init__(self, map: ScrollMap, server_url: str, client_data: JSON = {}) -> None:
        super().__init__(map)

        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.server_url = server_url
        # self.event_message_queue: asyncio.Queue = asyncio.Queue()
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

    # def _send_message(self, json_message: JSON) -> None:
    #     self.event_message_queue.put_nowait(json_message)
    #     # await self._websocket.send(message)

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

    # @self._rpc.register
    def add_actor_on_client(self, uuid: UUID, scene_uuid: UUID, image: str, central_actor: bool) -> None:
        actor = Actor(image, uuid=uuid)

        if scene_uuid != self.scene_uuid:
            # Foreign actor cannot be central
            central_actor = False

        self.add_actor(actor, central_actor)

    # @self._rpc.register
    def remove_actor_on_client(self, uuid: UUID) -> None:
        actor: Actor = self.get_actor(uuid)
        self.remove_actor(actor)

    # @self._rpc.register
    def on_actor_prop_change(self, uuid: UUID, props: Dict[str, Any]) -> None:
        # print(f"MultiplayerClient.on_actor_prop_change {self.scene_uuid}: {uuid} {prop}: {value}")
        actor = self.get_actor(uuid)
        for prop, value in props.items():
            actor.__setattr__(prop, value)

    # @self._rpc.register
    def on_screen_redraw(self, data: List[JSON]) -> None:
        self._screen_client.set_messages(data)
