import pygame

from pgz import actor

from .scene import EventDispatcher, Scene


class MapScene(Scene):
    def __init__(self, map):
        super().__init__()
        self.map = map
        self.central_actor = None

    def dispatch_event(self, event):
        # transfrom mouse positions
        if event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            view_pos = event.pos
            scene_pos = self.map.transform(view_pos)
            event.scene_pos = scene_pos
            event.pos = scene_pos
        super().dispatch_event(event)

    def draw(self, surface):
        if self.central_actor:
            # center the map/screen on our Ship
            self.map.set_center(self.central_actor.pos)

        self.map.draw(surface)

    def add_actor(self, actor, central_actor=False):
        if central_actor:
            self.central_actor = actor
        # add our ship to the group
        self.map.add_sprite(actor)

    def remove_actor(self, actor):
        if actor == self.central_actor:
            self.central_actor = None
        self.map.remove_sprite(actor)
