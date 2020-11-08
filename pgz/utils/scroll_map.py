from typing import Any, Dict, List, Optional, Tuple

import pygame
import pyscroll
import pyscroll.data
from pgzero.screen import Screen
from pyscroll.group import PyscrollGroup
from pytmx import TiledMap


def extract_collision_objects_from_object_layers(tmx_data: TiledMap) -> List[pygame.Rect]:
    collison_objects = list()
    for object in tmx_data.objects:
        collison_objects.append(pygame.Rect(object.x, object.y, object.width, object.height))

    return collison_objects


def extract_collision_objects_from_tile_layers(tmx_data: TiledMap, collision_layer_names: List[str]) -> List[pygame.Rect]:
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

    def __init__(self, screen_size: Tuple[int, int], tmx: TiledMap, collision_layers: List[str] = []) -> None:
        self._tmx = tmx

        # create new data source for pyscroll
        map_data = pyscroll.data.TiledMapData(self._tmx)

        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(map_data, screen_size, clamp_camera=False, tall_sprites=1)
        self.map_layer.zoom = 1

        # pyscroll supports layered rendering.  our map has 3 'under' layers
        # layers begin with 0, so the layers are 0, 1, and 2.
        # since we want the sprite to be on top of layer 1, we set the default
        # layer for sprites as 2
        self._map_group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)

        self._map_collision_obj: List[pygame.Rect] = []

        self.add_collision_layers(collision_layers)

    def add_collision_layers(self, collision_layers: List[str]) -> None:
        # setup level geometry with simple pygame rects, loaded from pytmx
        self._map_collision_obj += extract_collision_objects_from_tile_layers(self._tmx, collision_layers)

    def view(self) -> Any:
        return self._map_group.view

    def transform(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        return (pos[0] + self._map_group.view.left, pos[1] + self._map_group.view.top)

    def draw(self, screen: Screen) -> None:
        # draw the map and all sprites
        self._map_group.draw(screen.surface)

    def update(self, dt: float) -> None:
        """Tasks that occur over time should be handled here"""
        self._map_group.update(dt)

    def add_sprite(self, sprite: pygame.sprite.Sprite, group_name: str = "") -> None:
        self._map_group.add(sprite)

    def remove_sprite(self, sprite: pygame.sprite.Sprite) -> None:
        sprite.remove(self._map_group)

    def set_center(self, point: Tuple[int, int]) -> None:
        self._map_group.center(point)

    def get_center(self) -> Tuple[int, int]:
        if not self.map_layer.map_rect:
            raise Exception("Map was not configured properly")
        return self.map_layer.map_rect.center  # type: ignore

    def change_zoom(self, change: float) -> None:
        value = self.map_layer.zoom + change
        if value > 0:
            self.map_layer.zoom = value

    def set_size(self, size: Tuple[int, int]) -> None:
        self.map_layer.set_size(size)

    def collide_map(self, sprite: pygame.sprite.Sprite) -> bool:
        if not sprite.rect:
            return False
        return bool(sprite.rect.collidelist(self._map_collision_obj) > -1)
