from typing import Tuple

import pygame
import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup
from pytmx.util_pygame import load_pygame


def extract_collision_objects_from_object_layers(tmx_data):
    collison_objects = list()
    for object in tmx_data.objects:
        collison_objects.append(pygame.Rect(object.x, object.y, object.width, object.height))

    return collison_objects


def extract_collision_objects_from_tile_layers(tmx_data, collision_layer_names):
    collison_objects = list()

    for layer_name in collision_layer_names:
        collision_layer = tmx_data.get_layer_by_name(layer_name)
        for x in range(collision_layer.width):
            for y in range(collision_layer.height):
                image = tmx_data.get_tile_image(x, y, 1)
                if image:
                    collison_objects.append(
                        pygame.Rect(
                            x * tmx_data.tilewidth,
                            y * tmx_data.tileheight,
                            tmx_data.tilewidth,
                            tmx_data.tileheight,
                        )
                    )
    return collison_objects


class ScrollMap(object):
    """
    This class provides functionality:
    - create and manage a pyscroll group
    - load a collision layers
    - manage sprites added to the map
    - allows to detect collisions with loaded collision layers
    - render the map and the sprites on top
    """

    def __init__(self, screen_size, tmx, collision_layers):
        # setup level geometry with simple pygame rects, loaded from pytmx
        self.walls = extract_collision_objects_from_tile_layers(tmx, collision_layers)

        # create new data source for pyscroll
        map_data = pyscroll.data.TiledMapData(tmx)

        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(map_data, screen_size, clamp_camera=False, tall_sprites=1)
        self.map_layer.zoom = 1

        # pyscroll supports layered rendering.  our map has 3 'under' layers
        # layers begin with 0, so the layers are 0, 1, and 2.
        # since we want the sprite to be on top of layer 1, we set the default
        # layer for sprites as 2
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)

    def view(self):
        return self.group.view

    def transform(self, pos):
        return (pos[0] + self.group.view.left, pos[1] + self.group.view.top)

    def draw(self, surface):
        # draw the map and all sprites
        self.group.draw(surface)

    def update(self, dt):
        """Tasks that occur over time should be handled here"""
        self.group.update(dt)

    def collide(self, sprite):
        return sprite.rect.collidelist(self.walls) > -1

    def add_sprite(self, sprite):
        self.group.add(sprite)

    def remove_sprite(self, sprite: pygame.Surface):
        sprite.remove(self.group)

    def set_center(self, point: Tuple[int, int]):
        self.group.center(point)

    def get_center(self) -> Tuple[int, int]:
        return self.map_layer.map_rect.center

    def change_zoom(self, change: float) -> None:
        value = self.map_layer.zoom + change
        if value > 0:
            self.map_layer.zoom = value

    def set_size(self, size: Tuple[int, int]):
        self.map_layer.set_size(size)
