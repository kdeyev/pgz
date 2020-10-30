import asyncio
import json
from uuid import uuid4

import pygame
import websockets

from .actor import Actor
from .multiplayer_actor import MultiplayerActor, MultiplayerActorStub
from .rpc import Registrator, serialize_json_rpc
from .scene import Scene


class MultiplayerClientHeadlessScene:
    def __init__(self):
        super().__init__()
        self.map = None
        self.broadcast = None
        self.actor_factory = {}
        self.rpc = Registrator()

        @self.rpc.register
        def handle_client_event(event_type, attributes):
            event = pygame.event.Event(event_type, **attributes)
            self.handle_event(event)

    def handle_message(self, message):
        self.rpc.dispatch(message)

    def handle_event(self, event):
        pass
        # super().handle_event(event)

    def update(self, dt):
        self.map.update(dt)

    def broadcast_property_change(self, uuid, prop, value):
        message = serialize_json_rpc("on_actor_prop_change", (uuid, prop, value))
        self.broadcast(message)

    def create_actor(self, cls_name, *args, **kwargs):
        uuid = str(uuid4())
        actor = self.actor_factory[cls_name](uuid, self.remove_actor, *args, **kwargs)
        self.map.add_sprite(actor)

        message = serialize_json_rpc("create_actor_on_client", (uuid, actor.image_name))
        self.broadcast(message)

        return MultiplayerActorStub(actor, self.broadcast_property_change)

    def remove_actor(self, actor):
        uuid = str(uuid4())
        message = serialize_json_rpc("remove_actor_on_client", (uuid))
        self.broadcast(message)


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
            await asyncio.wait([client.send(message) for client in self.clients])

    def remove_actor(self, actor):
        self.map.remove_actor(actor)

    async def _register_client(self, websocket):
        scene = self.HeadlessSceneClass()
        scene.map = self.map
        scene.broadcast = self.broadcast

        self.clients[websocket] = scene

        scene.on_enter(None)
        # await notify_users()

    async def _unregister_client(self, websocket):
        scene = self.clients[websocket]
        scene.on_exit(None)
        self.clients.remove(websocket)
        # await notify_users()

    def _handle_client_message(self, websocket, message):
        self.clients[websocket].handle_message(message)

    async def _serve_client(self, websocket, path):
        # register(websocket) sends user_event() to websocket
        await self._register_client(websocket)
        try:
            async for message in websocket:
                message = json.loads(message)
                self._handle_client_message(websocket, message)
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
        # self.client_uuid = str(uuid4())
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
            self.map.remove_actor(actor)

        @self.rpc.register
        def on_actor_prop_change(uuid, prop, value):
            actor = self.actors[uuid]
            setattr(actor, prop, value)

    async def _send_message(self, message):
        await self._websocket.send(message)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            message = serialize_json_rpc("handle_client_event", (event.type, event.__dict__))
            asyncio.ensure_future(self._send_message(message))
            # self._websocket.send(message)

    async def connect_to_server(self, host: str = "localhost", port: int = 8765):
        self._websocket = await websockets.connect(f"ws://{host}:{port}")
        asyncio.ensure_future(self._handle_messages())

    async def _handle_messages(self):
        async for message in self._websocket:
            message = json.loads(message)
            self.rpc.dispatch(message)
