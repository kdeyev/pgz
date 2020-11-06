import asyncio
import json
import time
from re import A
from typing import Any, Callable, Dict, List, Optional, Tuple

# from re import T
from uuid import uuid4

import nest_asyncio
import pygame
import websockets

# import jsonrpc_base
from .actor import Actor
from .keyboard import Keyboard
from .map_scene import MapScene
from .rpc import SimpleRPC, serialize_json_array_from_queue, serialize_json_message
from .scene import EventDispatcher, Scene
from .screen_rpc import RPCScreenClient, RPCScreenServer

nest_asyncio.apply()

UUID = str
JSON = Dict[str, Any]


class MultiplayerActor(Actor):
    # DELEGATED_ATTRIBUTES = [a for a in dir(Actor) if not a.startswith("_")] + Actor.DELEGATED_ATTRIBUTES
    SEND = Actor.DELEGATED_ATTRIBUTES + ["angle", "image"]

    def __init__(self, image: str) -> None:
        super().__init__(image)
        self.uuid: UUID = f"{self.__class__.__name__}-{str(uuid4())}"

        self.client_uuid: UUID = ""
        self.deleter = None
        self.keyboard = None
        self._on_prop_change = None

    def __setattr__(self, attr: str, value: Any) -> None:
        if attr in self.__class__.SEND and hasattr(self, "_on_prop_change") and self._on_prop_change:
            if getattr(self, attr) != value:
                self._on_prop_change(self.uuid, attr, value)

        super().__setattr__(attr, value)

    def serialize_state(self):
        state = {}
        for attr in self.__class__.SEND:
            try:
                value = getattr(self, attr)
            except Exception as e:
                print(f"MultiplayerActor.serialize_state: {e}")
                continue

            try:
                json.dumps({attr: value})
            except Exception as e:
                print(f"MultiplayerActor.serialize_state: {e}")
                continue

            state[attr] = value
        return state


class MultiplayerClientHeadlessScene(EventDispatcher):
    def __init__(self):
        super().__init__()

        # The scene UUID is used for communication
        self._client_uuid = None
        # Map object, supposed to be headless: don't add sprites directly to there
        self._map = None
        # Callback for sending broadcast messages: Message will be received by all clients
        self._broadcast_message = None
        # List of the actors belonging to the scene. Different scenes will have different actors. But they are mixed together on the client-side for rendering
        self._actors: Dict[str, MultiplayerActor] = {}
        # Simple massages dispatcher
        self._rpc = SimpleRPC()
        # Local keyboard object: convenient class for chenking the current keyboard state. The keyboard state is updated based on event coming from the client
        self.keyboard = Keyboard()
        # Message buffer: messages are flushing periodically for preventing the network trashing
        self._message_queue = asyncio.Queue()
        # Client-side screen resolution
        self.resolution = (1, 1)
        # Client data is the data was provided by the client during the handshake: it's usually stuff like player name, avatar, etc
        self._client_data = {}

        # Call EventDispatcher.load_handlers method for setting convenient event shortcuts like on_mouse_down, etc
        self.load_handlers()

        # Bind event message handler
        @self._rpc.register("handle_client_event")
        def handle_client_event(event_type, attributes: JSON):
            # Deserialize event
            event = pygame.event.Event(event_type, **attributes)

            # Update local keyboard helper
            if event.type == pygame.KEYDOWN:
                self.keyboard._press(event.key)
            if event.type == pygame.KEYUP:
                self.keyboard._release(event.key)

            # Handle client-side screen resolution change
            if event.type == pygame.VIDEORESIZE:
                self.resolution = (event.w, event.h)

            # Dispatch events thru EventDispatcher
            try:
                self.dispatch_event(event)
            except Exception as e:
                print(f"handle_client_event: {e}")

    def init_scene_(self, client_uuid: UUID, map, _broadcast_message: Callable[[JSON], None]):
        """
        Server API:
        Scene initialization by the server
        """
        self._client_uuid = client_uuid
        self._map = map
        self._broadcast_message = _broadcast_message

    def recv_handshake_(self, massage: JSON):
        """
        Server API:
        Handle handshake message called by server
        """
        self.resolution = massage["resolution"]
        self._client_data = massage["client_data"]

    def redraw_(self):
        """
        Server API
        Handle scene redraw called by server event loop
        """
        # self._screen.clear()
        self.draw(self._screen)
        changed, data = self._screen.get_messages()
        if changed:
            json_message = serialize_json_message("on_screen_redraw", data)
            self._send_message(json_message)

    def handle_message_(self, message: JSON):
        """
        Server API:
        Handle event message coming from the client
        """
        try:
            self._rpc.dispatch(message)
        except Exception as e:
            print(f"handle_message_: {e}")

    def remove_all_actors_(self):
        """
        Server API:
        Remove all actors from the scene.
        """
        for actor in self._actors.values():
            self._remove_actor(actor)

        self._actors = {}

    def _remove_actor(self, actor):
        """
        Remove an actor from the scene and send message to clients.
        """
        uuid = actor.uuid
        self._map.remove_sprite(actor.sprite_delegate)
        json_message = serialize_json_message("remove_actor_on_client", uuid)
        self._broadcast_message(json_message)

    def _send_message(self, json_message):
        """
        Send message to the client fo the scene.
        """
        self._message_queue.put_nowait(json_message)

    def _broadcast_property_change(self, uuid: str, prop: str, value: Any):
        """
        Send message about actor's property change.
        """
        json_message = serialize_json_message("on_actor_prop_change", uuid, prop, value)
        self._broadcast_message(json_message)

    @property
    def actors_(self):
        """
        Server API:
        Get dictionary of actors
        """
        return self._actors

    @property
    def screen(self):
        """
        Get RPCScreenServer screen object, which mimics to the Screen API. Any modification of the object will be reflected on the client screen.
        """
        return self._screen

    @property
    def map(self):
        """
        Get ScrollMap object.
        """
        return self._map

    @property
    def client_uuid(self) -> str:
        """
        Get client UUID.
        """
        return self._client_uuid

    @property
    def resolution(self):
        """
        Get resolution of the client's screen. Client sends notifications about the client screen size changes.
        Screen object (self.screen) will be updated according to the notifications.
        """
        return self._screen.surface.get_size()

    @resolution.setter
    def resolution(self, value):
        """
        Server API:
        Modify the client's screen resolution. This method will be called by the server internally
        Screen object (self.screen) will be updated according to the notifications.
        """
        self._screen = RPCScreenServer(value)

    @property
    def client_data(self) -> JSON:
        """
        Get data provided by cleint side.
        """
        return self._client_data

    def draw(self, screen):
        """Override this with the scene drawing.

        :param pygame.Surface screen: screen to draw the scene on
        """

    def on_enter(self, previous_scene=None):
        """Override this to initialize upon scene entering.

        The :attr:`application` property is initialized at this point,
        so you are free to access it through ``self.application``.
        Stuff like changing resolution etc. should be done here.

        If you override this method and want to use class variables
        to change the application's settings, you must call
        ``super().on_enter(previous_scene)`` in the subclass.

        :param Scene|None previous_scene: previous scene to run
        """

    def on_exit(self, next_scene=None):
        """Override this to deinitialize upon scene exiting.

        The :attr:`application` property is still initialized at this
        point. Feel free to do saving, settings reset, etc. here.

        :param Scene|None next_scene: next scene to run
        """

    def handle_event(self, event):
        """Override this to handle an event in the scene.

        All of :mod:`pygame`'s events are sent here, so filtering
        should be applied manually in the subclass.

        :param pygame.event.Event event: event to handle
        """

    def update(self, dt):
        """Override this with the scene update tick.

        :param int dt: time in milliseconds since the last update
        """

    def add_actor(self, actor, central_actor=False):
        """
        Add actor to the scene and send notifications to the  clients.

        If central_actor is True, client's camera will track the actor position. You can have only one central actor on the scene.
        """

        actor.client_uuid = self.client_uuid
        actor.deleter = self.remove_actor
        actor.keyboard = self.keyboard
        actor._on_prop_change = self._broadcast_property_change
        self._actors[actor.uuid] = actor
        self._map.add_sprite(actor.sprite_delegate)

        json_message = serialize_json_message("add_actor_on_client", actor.uuid, self.client_uuid, actor.image, central_actor)
        self._broadcast_message(json_message)

        return actor

    def remove_actor(self, actor):
        """
        Remore actor from the scene and send notifications to the  clients.
        """

        self._remove_actor(actor)

        uuid = actor.uuid
        del self._actors[uuid]


class MultiplayerSceneServer:
    def __init__(self, map, HeadlessSceneClass):
        super().__init__()

        # The map object will be shared between all the headless scenes
        self._map = map
        # Dict of connected clients
        self._clients = {}

        # Class of the headless scenes. Server will instantiate a scene object per connected client
        assert issubclass(HeadlessSceneClass, MultiplayerClientHeadlessScene)
        self._HeadlessSceneClass = HeadlessSceneClass

    def update(self, dt):
        self._map.update(dt)
        for scenes in self._clients.values():
            scenes.update(dt)

        # server calls internal redraw
        for scenes in self._clients.values():
            scenes.redraw_()
        asyncio.ensure_future(self._flush_messages())

    def _broadcast_message(self, json_message):
        for scene in self._clients.values():
            scene._message_queue.put_nowait(json_message)

    async def _flush_messages(self):
        if self._clients:  # asyncio.wait doesn't accept an empty list
            try:
                send_events = []
                for websocket, scene in self._clients.items():
                    # There are messages in the queue
                    if not scene._message_queue.empty():
                        # create one json array
                        message = serialize_json_array_from_queue(scene._message_queue)
                        # send broadcast
                        send_event = websocket.send(message)
                        send_events.append(send_event)

                # wait for all events
                if send_events:
                    await asyncio.wait(send_events)
            except Exception as e:
                print(f"MultiplayerSceneServer._broadcast: {e}")

    async def _recv_handshake(self, websocket, scene):
        massage = await websocket.recv()
        massage = json.loads(massage)
        scene.recv_handshake_(massage)

    async def _send_handshake(self, websocket, scene):
        actors = []
        for sc in self._clients.values():
            actors += sc.actors_.values()

        actors_states = {actor.uuid: actor.serialize_state() for actor in actors}
        massage = {"uuid": scene.client_uuid, "actors_states": actors_states, "screen_state": scene.screen.get_messages()}
        massage = json.dumps(massage)
        await websocket.send(massage)

    async def _register_client(self, websocket):
        client_uuid = f"{self._HeadlessSceneClass.__name__}-{str(uuid4())}"

        # Create a headless scene
        scene = self._HeadlessSceneClass()
        # Create init the scene
        scene.init_scene_(client_uuid, self._map, self._broadcast_message)

        await self._recv_handshake(websocket, scene)
        await self._send_handshake(websocket, scene)

        # scene.start_update_loop(update_rate=self.update_rate)

        self._clients[websocket] = scene
        scene.on_enter(None)

    async def _unregister_client(self, websocket):
        scene = self._clients[websocket]

        # First of all remove dead client
        del self._clients[websocket]

        scene.on_exit(None)
        # scene.stop_update_loop()
        scene.remove_all_actors_()
        # await notify_users()

    def _handle_client_message(self, websocket, message):
        try:
            self._clients[websocket].handle_message_(message)
        except Exception as e:
            print(f"_handle_client_message: {e}")

    async def _serve_client(self, websocket, path):
        # register(websocket) sends user_event() to websocket
        await self._register_client(websocket)
        try:
            async for message in websocket:
                try:
                    message = json.loads(message)
                    self._handle_client_message(websocket, message)
                except Exception as e:
                    print(f"_serve_client: {e}")
        finally:
            await self._unregister_client(websocket)

    def start_server(self, host: str = "localhost", port: int = 8765):
        self._server_task = asyncio.ensure_future(websockets.serve(self._serve_client, host, port))
        # self._flush_messages_task = asyncio.ensure_future(self._flush_messages_loop())

    def stop_server(self):
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
    def __init__(self, map, server_url, client_data={}):
        super().__init__(map)
        self._actors: Dict[str, Actor] = {}
        self.central_actor: Optional[Actor] = None
        self.client_uuid = None
        self._websocket = None
        self.server_url = server_url
        self._rpc = SimpleRPC()
        self.event_message_queue = asyncio.Queue()
        self._screen_client = RPCScreenClient()
        self._client_data = client_data

    def on_exit(self, next_scene):
        super().on_exit(next_scene)

        if self._websocket:
            asyncio.get_event_loop().run_until_complete(self._websocket.close())
            self._websocket = None

    def on_enter(self, previous_scene: Scene) -> None:
        super().on_enter(previous_scene)

        asyncio.get_event_loop().run_until_complete(self.connect_to_server())
        if not self._websocket:
            raise Exception("Cannot connect")

        @self._rpc.register
        def add_actor_on_client(uuid, client_uuid, image, central_actor):
            actor = Actor(image)
            self._actors[uuid] = actor

            if client_uuid != self.client_uuid:
                # Foreign actor cannot be central
                central_actor = False

            self.add_actor(actor, central_actor)

        @self._rpc.register
        def remove_actor_on_client(uuid: UUID) -> None:
            actor: Actor = self._actors[uuid]
            del self._actors[uuid]
            self.remove_actor(actor)

        @self._rpc.register
        def on_actor_prop_change(uuid, prop, value):
            # print(f"MultiplayerClient.on_actor_prop_change {self.client_uuid}: {uuid} {prop}: {value}")
            actor = self._actors[uuid]
            actor.__setattr__(prop, value)

        @self._rpc.register
        def on_screen_redraw(data: List[JSON]) -> None:
            self._screen_client.set_messages(data)

    def update(self, dt: float):
        asyncio.ensure_future(self._flush_messages())
        super().update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        super().draw(screen)
        self._screen_client.draw(self.screen)
        self.screen.draw.text(self.server_url, pos=(300, 0))

    def _send_message(self, json_message: JSON) -> None:
        self.event_message_queue.put_nowait(json_message)
        # await self._websocket.send(message)

    async def _flush_messages(self) -> None:
        if not self.event_message_queue.empty():
            # create one json array
            message = serialize_json_array_from_queue(self.event_message_queue)
            # send message
            await self._websocket.send(message)

    def handle_event(self, event) -> None:

        # this will be handled if the window is resized
        if event.type == pygame.VIDEORESIZE:
            self.map.set_size((event.w, event.h))
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_EQUALS:
                self.map.change_zoom(0.25)
            elif event.key == pygame.K_MINUS:
                self.map.change_zoom(-0.25)

        if not self._websocket:
            # not connected yet
            return

        try:
            json_message = serialize_json_message("handle_client_event", event.type, event.__dict__)
        except Exception as e:
            print(f"handle_event: {e}")
            return
        self._send_message(json_message)

    async def connect_to_server(self, attempts=10) -> bool:
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
        massage = {"resolution": list(self.resolution), "client_data": self._client_data}
        await websocket.send(json.dumps(massage))

    async def _recv_handshake(self, websocket: websockets.WebSocketClientProtocol) -> None:
        data = await websocket.recv()
        massage = json.loads(data)

        self.client_uuid = massage["uuid"]
        actors_states: Dict[UUID, JSON] = massage["actors_states"]
        uuid: UUID
        state: JSON
        for uuid, state in actors_states.items():
            image = state["image"]
            actor = Actor(image)
            for attr, value in state.items():
                setattr(actor, attr, value)

            self._actors[uuid] = actor
            self.add_actor(actor)

    async def _handle_messages(self) -> None:
        message: str
        async for message in self._websocket:
            try:
                json_messages: JSON = json.loads(message)
                self._rpc.dispatch(json_messages)
            except Exception as e:
                print(f"_handle_messages: {e}")

    # def on_key_down(self, key):
    #     if key == pygame.K_EQUALS:
    #         self._map.change_zoom(0.25)
    #     elif key == pygame.K_MINUS:
    #         self._map.change_zoom(-0.25)
