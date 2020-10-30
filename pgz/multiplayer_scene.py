import asyncio
import json
from uuid import uuid4

import pygame
import websockets

from .actor import Actor
from .keyboard import Keyboard
from .rpc import Registrator, serialize_json_rpc
from .scene import EventDispatcher, Scene


class MultiplayerActor(Actor):
    DELEGATED_ATTRIBUTES = [a for a in dir(Actor) if not a.startswith("_")] + Actor.DELEGATED_ATTRIBUTES

    def __init__(self, image_name, uuid, deleter):
        super().__init__(image_name)
        self.uuid = uuid
        self.deleter = deleter
        self.keyboard = None
        self._on_prop_change = None

    def __setattr__(self, attr, value):
        if attr in self.__class__.DELEGATED_ATTRIBUTES and hasattr(self, "_on_prop_change") and self._on_prop_change:
            if getattr(self, attr) != value:
                self._on_prop_change(self.uuid, attr, value)

        super().__setattr__(attr, value)

    def get_state_message(self):
        state = {}
        for attr in self.__class__.DELEGATED_ATTRIBUTES:
            try:
                value = getattr(self, attr)
            except Exception as e:
                print(f"MultiplayerActor.get_state_message: {e}")
                continue

            try:
                json.dumps({attr: value})
            except Exception as e:
                print(f"MultiplayerActor.get_state_message: {e}")
                continue

            state[attr] = value
        return state


class MultiplayerClientHeadlessScene(EventDispatcher):
    def __init__(self):
        super().__init__()
        self.uuid = None
        self.map = None
        self.broadcast = None
        self.actor_factory = {}
        self.actors = {}
        self.rpc = Registrator()
        self.keyboard = Keyboard()

        self.load_handlers()

        @self.rpc.register
        def handle_client_event(event_type, attributes):
            event = pygame.event.Event(event_type, **attributes)
            if event.type == pygame.KEYDOWN:
                self.keyboard._press(event.key)
            elif event.type == pygame.KEYUP:
                self.keyboard._release(event.key)

            try:
                self.dispatch_event(event)
            except Exception as e:
                print(f"handle_client_event: {e}")

    def handle_message(self, message):
        try:
            self.rpc.dispatch(message)
        except Exception as e:
            print(f"handle_message: {e}")

    def on_enter(self, previous_scene=None):
        pass

    def on_exit(self, next_scene=None):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        self.map.update(dt)

    def broadcast_property_change(self, uuid, prop, value):
        message = serialize_json_rpc("on_actor_prop_change", (uuid, prop, value))
        self.broadcast(message)

    def create_actor(self, cls_name, *args, **kwargs):
        uuid = f"{cls_name}-{str(uuid4())}"
        actor = self.actor_factory[cls_name](uuid, self.remove_actor, *args, **kwargs)
        actor.keyboard = self.keyboard
        actor._on_prop_change = self.broadcast_property_change
        self.actors[uuid] = actor
        self.map.add_sprite(actor)

        message = serialize_json_rpc("create_actor_on_client", (uuid, actor.image_name))
        self.broadcast(message)

        return actor

    def _remove_actor(self, actor):
        uuid = actor.uuid
        self.map.remove_sprite(actor)
        message = serialize_json_rpc("remove_actor_on_client", (uuid,))
        self.broadcast(message)

    def remove_actor(self, actor):
        self._remove_actor(actor)

        uuid = actor.uuid
        del self.actors[uuid]

    def remove_all_actors(self):
        for actor in self.actors.values():
            self._remove_actor(actor)

        self.actors = {}


class MultiplayerSceneServer:
    def __init__(self, map, HeadlessSceneClass):
        super().__init__()
        self.map = map
        self.clients = {}

        assert issubclass(HeadlessSceneClass, MultiplayerClientHeadlessScene)
        self.HeadlessSceneClass = HeadlessSceneClass

    def broadcast(self, message):
        asyncio.ensure_future(self._broadcast(message))

    async def _broadcast(self, message):
        if self.clients:  # asyncio.wait doesn't accept an empty list
            try:
                await asyncio.wait([client.send(message) for client in self.clients])
            except Exception as e:
                print(f"MultiplayerSceneServer._broadcast: {e}")

    # def remove_actor(self, actor):
    #     self.map.remove_sprite(actor)

    async def _send_handshake(self, websocket, uuid):
        actors = []
        for scene in self.clients.values():
            actors += scene.actors.values()

        actors_states = {actor.uuid: actor.get_state_message() for actor in actors}
        massage = {"uuid": uuid, "actors_states": actors_states}
        massage = json.dumps(massage)
        await websocket.send(massage)

    async def _register_client(self, websocket):
        uuid = f"{self.HeadlessSceneClass.__name__}-{str(uuid4())}"

        scene = self.HeadlessSceneClass()
        scene.map = self.map
        scene.broadcast = self.broadcast
        scene.uuid = uuid

        await self._send_handshake(websocket, uuid)

        self.clients[websocket] = scene
        scene.on_enter(None)

    async def _unregister_client(self, websocket):
        scene = self.clients[websocket]

        # First of all remove dead client
        del self.clients[websocket]

        scene.on_exit(None)
        scene.remove_all_actors()
        # await notify_users()

    def _handle_client_message(self, websocket, message):
        try:
            self.clients[websocket].handle_message(message)
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
        asyncio.ensure_future(websockets.serve(self._serve_client, host, port))

    def update(self, dt):
        for scenes in self.clients.values():
            scenes.update(dt)


class MultiplayerClient(Scene):
    def __init__(self, map):
        super().__init__()
        self.map = map
        self.actors = {}
        self.uuid = None
        self._websocket = None
        self.rpc = Registrator()

    def draw(self, surface):
        self.map.draw(surface)
        super().draw(surface)

    def on_exit(self, next_scene):
        super().on_exit(next_scene)

    def on_enter(self, previous_scene):
        super().on_enter(previous_scene)

        @self.rpc.register
        def create_actor_on_client(uuid, image_name):
            actor = Actor(image_name)
            self.actors[uuid] = actor
            self.map.add_sprite(actor)

        @self.rpc.register
        def remove_actor_on_client(uuid):
            actor = self.actors[uuid]
            del self.actors[uuid]
            self.map.remove_sprite(actor)

        @self.rpc.register
        def on_actor_prop_change(uuid, prop, value):
            print(f"MultiplayerClient.on_actor_prop_change {self.uuid}: {uuid} {prop}: {value}")
            actor = self.actors[uuid]
            setattr(actor, prop, value)

    async def _send_message(self, message):
        await self._websocket.send(message)

    def handle_event(self, event):
        if not self._websocket:
            # not connected yet
            return

        if event.type in [pygame.MOUSEMOTION, pygame.KEYDOWN, pygame.KEYUP]:
            print(f"MultiplayerClient.handle_event {self.uuid}: {event.__class__.__name__} {event.type} {event.__dict__}")
            message = serialize_json_rpc("handle_client_event", (event.type, event.__dict__))
            asyncio.ensure_future(self._send_message(message))
            # self._websocket.send(message)

    async def connect_to_server(self, host: str = "localhost", port: int = 8765):
        websocket = await websockets.connect(f"ws://{host}:{port}")
        await self._receive_handshake(websocket)
        asyncio.ensure_future(self._handle_messages(websocket))

    async def _receive_handshake(self, websocket):
        massage = await websocket.recv()
        massage = json.loads(massage)

        self.uuid = massage["uuid"]
        actors_states = massage["actors_states"]
        for uuid, state in actors_states.items():
            image_name = state["image_name"]
            actor = Actor(image_name)
            for attr, value in state.items():
                setattr(actor, attr, value)

            self.actors[uuid] = actor
            self.map.add_sprite(actor)

    async def _handle_messages(self, websocket):
        self._websocket = websocket
        async for message in self._websocket:
            try:
                message = json.loads(message)
                self.rpc.dispatch(message)
            except Exception as e:
                print(f"_handle_messages: {e}")
