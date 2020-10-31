import pygame

from .scene import EventDispatcher, Scene


class MapScene(Scene):
    def __init__(self, map):
        super().__init__()
        self.map = map

    def dispatch_event(self, event):
        # if event.type in [pygame.MOUSEMOTION, pygame.KEYDOWN, pygame.KEYUP]:
        if event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL]:
            view_pos = event.pos
            scene_pos = self.map.transform(view_pos)
            event.pos = scene_pos
        super().dispatch_event(event)
