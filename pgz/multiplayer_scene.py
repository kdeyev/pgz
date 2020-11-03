import asyncio
import json
import time
from typing import Tuple

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
from .scene import EventDispatcher
from .screen_rpc import RPCScreenClient, RPCScreenServer

nest_asyncio.apply()


class MultiplayerActor(Actor):
    # DELEGATED_ATTRIBUTES = [a for a in dir(Actor) if not a.startswith("_")] + Actor.DELEGATED_ATTRIBUTES
    SEND = Actor.DELEGATED_ATTRIBUTES + ["angle", "image_name"]

    def __init__(self, image_name):
        super().__init__(image_name)
        self.uuid = f"{self.__class__.__name__}-{str(uuid4())}"

        self.client_uuid = None
        self.deleter = None
        self.keyboard = None
        self._on_prop_change = None

    def __setattr__(self, attr, value):
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
        self.uuid = None
        self.map = None
        self.broadcast_message = None
        self.actors = {}
        self.rpc = SimpleRPC()
        self.keyboard = Keyboard()

        self.message_queue = asyncio.Queue()

        # TODO
        self.resolution = (1600, 1200)

        self.load_handlers()

        @self.rpc.register
        def handle_client_event(event_type, attributes):
            # Deserialize event
            event = pygame.event.Event(event_type, **attributes)

            # Update local keyboard helper
            if event.type == pygame.KEYDOWN:
                self.keyboard._press(event.key)
            elif event.type == pygame.KEYUP:
                self.keyboard._release(event.key)

            # Dispatch events thru EventDispatcher
            try:
                self.dispatch_event(event)
            except Exception as e:
                print(f"handle_client_event: {e}")

    @property
    def screen(self):
        return self._screen

    @property
    def resolution(self):
        return self._screen.surface.get_size()

    @resolution.setter
    def resolution(self, value):
        self._screen = RPCScreenServer(value)

    def redraw(self):
        # self._screen.clear()
        self.draw(self._screen)
        changed, data = self._screen._get_messages()
        if changed:
            json_message = serialize_json_message("on_screen_redraw", data)
            self.send_message(json_message)

    def draw(self, screen):
        screen.draw.text(text="from server", pos=(500, 0))

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

    # def start_update_loop(self, update_rate):
    #     self.update_loop_task = asyncio.ensure_future(self._update_loop(update_rate))

    # def stop_update_loop(self):
    #     self.update_loop_task.cancel()

    # async def _update_loop(self, update_rate):
    #     current_time = time.time()
    #     while True:
    #         last_time, current_time = current_time, time.time()
    #         dt = 1 / update_rate - (current_time - last_time)
    #         await asyncio.sleep(dt)  # tick
    #         self.update(dt)

    def update(self, dt):
        pass

    def broadcast_property_change(self, uuid, prop, value):
        json_message = serialize_json_message("on_actor_prop_change", uuid, prop, value)
        self.broadcast_message(json_message)

    def add_actor(self, actor, central_actor=False):
        actor.client_uuid = self.uuid
        actor.deleter = self.remove_actor
        actor.keyboard = self.keyboard
        actor._on_prop_change = self.broadcast_property_change
        self.actors[actor.uuid] = actor
        self.map.add_sprite(actor)

        json_message = serialize_json_message("add_actor_on_client", actor.uuid, self.uuid, actor.image_name, central_actor)
        self.broadcast_message(json_message)

        return actor

    def _remove_actor(self, actor):
        uuid = actor.uuid
        self.map.remove_sprite(actor)
        json_message = serialize_json_message("remove_actor_on_client", uuid)
        self.broadcast_message(json_message)

    def remove_actor(self, actor):
        self._remove_actor(actor)

        uuid = actor.uuid
        del self.actors[uuid]

    def remove_all_actors(self):
        for actor in self.actors.values():
            self._remove_actor(actor)

        self.actors = {}

    def send_message(self, json_message):
        self.message_queue.put_nowait(json_message)


class MultiplayerSceneServer:
    def __init__(self, map, HeadlessSceneClass):
        super().__init__()
        self.map = map
        self.clients = {}

        self.update_rate = 20

        assert issubclass(HeadlessSceneClass, MultiplayerClientHeadlessScene)
        self.HeadlessSceneClass = HeadlessSceneClass

    def update(self, dt):
        self.map.update(dt)
        for scenes in self.clients.values():
            scenes.update(dt)

        # server calls internal redraw
        for scenes in self.clients.values():
            scenes.redraw()
        asyncio.ensure_future(self._flush_messages())

    def broadcast_message(self, json_message):
        for scene in self.clients.values():
            scene.message_queue.put_nowait(json_message)

    async def _flush_messages(self):
        if self.clients:  # asyncio.wait doesn't accept an empty list
            try:
                send_events = []
                for websocket, scene in self.clients.items():
                    # There are messages in the queue
                    if not scene.message_queue.empty():
                        # create one json array
                        message = serialize_json_array_from_queue(scene.message_queue)
                        # send broadcast
                        send_event = websocket.send(message)
                        send_events.append(send_event)

                # wait for all events
                if send_events:
                    await asyncio.wait(send_events)
            except Exception as e:
                print(f"MultiplayerSceneServer._broadcast: {e}")

    async def _send_handshake(self, websocket, uuid):
        actors = []
        for scene in self.clients.values():
            actors += scene.actors.values()

        actors_states = {actor.uuid: actor.serialize_state() for actor in actors}
        massage = {"uuid": uuid, "actors_states": actors_states}
        massage = json.dumps(massage)
        await websocket.send(massage)

    async def _register_client(self, websocket):
        uuid = f"{self.HeadlessSceneClass.__name__}-{str(uuid4())}"

        scene = self.HeadlessSceneClass()
        scene.map = self.map
        scene.broadcast_message = self.broadcast_message
        scene.uuid = uuid

        await self._send_handshake(websocket, uuid)

        # scene.start_update_loop(update_rate=self.update_rate)

        self.clients[websocket] = scene
        scene.on_enter(None)

    async def _unregister_client(self, websocket):
        scene = self.clients[websocket]

        # First of all remove dead client
        del self.clients[websocket]

        scene.on_exit(None)
        # scene.stop_update_loop()
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
    def __init__(self, map, server_url):
        super().__init__(map)
        self.actors = {}
        self.central_actor = None
        self.uuid = None
        self._websocket = None
        self.server_url = server_url
        self.rpc = SimpleRPC()
        self.event_message_queue = asyncio.Queue()
        self._screen_client = RPCScreenClient()

    def on_exit(self, next_scene):
        super().on_exit(next_scene)

        if self._websocket:
            asyncio.get_event_loop().run_until_complete(self._websocket.close())
            self._websocket = None

    def on_enter(self, previous_scene):
        super().on_enter(previous_scene)

        asyncio.get_event_loop().run_until_complete(self.connect_to_server())
        if not self._websocket:
            raise Exception("Cannot connect")

        @self.rpc.register
        def add_actor_on_client(uuid, client_uuid, image_name, central_actor):
            actor = Actor(image_name)
            self.actors[uuid] = actor

            if client_uuid != self.uuid:
                # Foreign actor cannot be central
                central_actor = False

            self.add_actor(actor, central_actor)

        @self.rpc.register
        def remove_actor_on_client(uuid):
            actor = self.actors[uuid]
            del self.actors[uuid]
            self.remove_actor(actor)

        @self.rpc.register
        def on_actor_prop_change(uuid, prop, value):
            # print(f"MultiplayerClient.on_actor_prop_change {self.uuid}: {uuid} {prop}: {value}")
            actor = self.actors[uuid]
            actor.__setattr__(prop, value)

        @self.rpc.register
        def on_screen_redraw(data):
            self._screen_client.set_messages(data)

    def update(self, dt):
        asyncio.ensure_future(self._flush_messages())
        super().update(dt)

    def draw(self, screen):
        super().draw(screen)
        self._screen_client.draw(self.screen)
        self.screen.draw.text(self.server_url, pos=(300, 0))

    def _send_message(self, json_message):
        self.event_message_queue.put_nowait(json_message)
        # await self._websocket.send(message)

    async def _flush_messages(self):
        if not self.event_message_queue.empty():
            # create one json array
            message = serialize_json_array_from_queue(self.event_message_queue)
            # send message
            await self._websocket.send(message)

    def handle_event(self, event):

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

    async def connect_to_server(self, attempts=10):
        websocket = None

        for attempt in range(attempts):
            try:
                websocket = await websockets.connect(self.server_url)
                break
            except OSError as e:
                print(f"handle_event: {e}")
                asyncio.sleep(1)
        if websocket:
            await self._receive_handshake(websocket)
            asyncio.ensure_future(self._handle_messages())
            return True
        else:
            return False

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
            self.add_actor(actor)
        self._websocket = websocket

    async def _handle_messages(self):
        async for message in self._websocket:
            try:
                json_messages = json.loads(message)
                self.rpc.dispatch(json_messages)
            except Exception as e:
                print(f"_handle_messages: {e}")

    # def on_key_down(self, key):
    #     if key == pygame.K_EQUALS:
    #         self.map.change_zoom(0.25)
    #     elif key == pygame.K_MINUS:
    #         self.map.change_zoom(-0.25)
