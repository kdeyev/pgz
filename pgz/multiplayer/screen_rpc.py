from typing import Any, Dict, List, Optional, Tuple

import pygame
from dictdiffer import diff, patch, revert, swap
from pgzero.rect import RECT_CLASSES, ZRect
from pgzero.screen import Screen, make_color, ptext, round_pos

from .rpc import SimpleRPC, serialize_json_message

JSON = Dict[str, Any]


class RPCSurfacePainter:
    """
    Interface to pygame.draw that is bound to a surface.
    """

    def __init__(self, massages: List[JSON]) -> None:
        self._messages = massages

    def line(self, start: Tuple[Any, Any], end: Tuple[Any, Any], color: Any, width: int = 1) -> None:
        """Draw a line from start to end."""
        start = round_pos(start)
        end = round_pos(end)

        self._messages.append(serialize_json_message("draw.line", (make_color(color), start, end, width)))
        # pygame.draw.line(self._surf, make_color(color), start, end, width)

    def circle(self, pos: Tuple[Any, Any], radius: float, color: Any, width: int = 1) -> None:
        """Draw a circle."""
        pos = round_pos(pos)
        self._messages.append(serialize_json_message("draw.circle", (make_color(color), pos, radius, width)))
        # pygame.draw.circle(self._surf, make_color(color), pos, radius, width)

    def filled_circle(self, pos: Tuple[Any, Any], radius: float, color: Any) -> None:
        """Draw a filled circle."""
        pos = round_pos(pos)
        self._messages.append(serialize_json_message("draw.circle", (make_color(color), pos, radius, 0)))
        # pygame.draw.circle(self._surf, make_color(color), pos, radius, 0)

    def polygon(self, points: List[Tuple[Any, Any]], color: Any) -> None:
        """Draw a polygon."""
        try:
            iter(points)
        except TypeError:
            raise TypeError("screen.draw.filled_polygon() requires an iterable of points to draw") from None  # noqa
        points = [round_pos(point) for point in points]
        self._messages.append(serialize_json_message("draw.polygon", (make_color(color), points, 1)))
        # pygame.draw.polygon(self._surf, make_color(color), points, 1)

    def filled_polygon(self, points: List[Tuple[Any, Any]], color: Any) -> None:
        """Draw a filled polygon."""
        try:
            iter(points)
        except TypeError:
            raise TypeError("screen.draw.filled_polygon() requires an iterable of points to draw") from None  # noqa
        points = [round_pos(point) for point in points]
        self._messages.append(serialize_json_message("draw.polygon", (make_color(color), points, 0)))
        # pygame.draw.polygon(self._surf, make_color(color), points, 0)

    def rect(self, rect: ZRect, color: Any, width: int = 1) -> None:
        """Draw a rectangle."""
        if not isinstance(rect, RECT_CLASSES):
            raise TypeError("screen.draw.rect() requires a rect to draw")
        self._messages.append(serialize_json_message("draw.rect", make_color(color), (rect.x, rect.y, rect.w, rect.h), width))
        # pygame.draw.rect(self._surf, make_color(color), rect, width)

    def filled_rect(self, rect: ZRect, color: Any) -> None:
        """Draw a filled rectangle."""
        if not isinstance(rect, RECT_CLASSES):
            raise TypeError("screen.draw.filled_rect() requires a rect to draw")
        self._messages.append(serialize_json_message("draw.rect", make_color(color), (rect.x, rect.y, rect.w, rect.h), 0))
        # pygame.draw.rect(self._surf, make_color(color), rect, 0)

    def text(self, *args: Any, **kwargs: Any) -> None:
        """Draw text to the screen."""
        # FIXME: expose ptext parameters, for autocompletion and autodoc
        self._messages.append(serialize_json_message("ptext.draw", args=args, kwargs=kwargs))
        # ptext.draw(*args, surf=self._surf, **kwargs)

    def textbox(self, *args: Any, **kwargs: Any) -> None:
        """Draw text to the screen, wrapped to fit a box"""
        # FIXME: expose ptext parameters, for autocompletion and autodoc
        self._messages.append(serialize_json_message("ptext.drawbox", args=args, kwargs=kwargs))
        # ptext.drawbox(*args, surf=self._surf, **kwargs)


class RPCScreenServer:
    def __init__(self, size: Tuple[int, int]) -> None:
        super().__init__()
        self._size = size
        self._prev_messages: List[JSON] = []
        self._messages: List[JSON] = []

        self.width, self.height = size

    def get_messages(self) -> Tuple[bool, List[JSON]]:

        if self._prev_messages == self._messages:
            self._messages.clear()
            return False, []

        self._prev_messages = self._messages[:]
        self._messages.clear()
        return True, self._prev_messages[:]

    def bounds(self) -> ZRect:
        """Return a Rect representing the bounds of the screen."""
        return ZRect((0, 0), (self.width, self.height))

    def clear(self) -> None:
        """Clear the screen to black."""
        self._messages.append(serialize_json_message("fill", (0, 0, 0)))
        # self.fill((0, 0, 0))

    def fill(self, color: Any, gcolor: Any = None) -> None:
        self._messages.append(serialize_json_message("fill", (color, gcolor)))

        # """Fill the screen with a colour."""
        # if gcolor:
        #     start = make_color(color)
        #     stop = make_color(gcolor)
        #     pixs = pygame.surfarray.pixels3d(self.surface)
        #     h = self.height

        #     gradient = np.dstack([np.linspace(a, b, h) for a, b in zip(start, stop)][:3])
        #     pixs[...] = gradient
        # else:
        #     self.surface.fill(make_color(color))

    def blit(self, image: str, pos: Tuple[int, int]) -> None:
        self._messages.append(serialize_json_message("blit", (image, pos)))
        # if isinstance(image, str):
        #     image = loaders.images.load(image)
        # self.surface.blit(image, pos)

    @property
    def resolution(self) -> Tuple[int, int]:
        return self._size

    @property
    def draw(self) -> RPCSurfacePainter:
        return RPCSurfacePainter(self._messages)

    def __repr__(self) -> str:
        return "<RPCScreenServer width={} height={}>".format(self.width, self.height)


class RPCScreenClient:
    def __init__(self) -> None:
        self._messages: List[JSON] = []
        self._surf: Optional[Screen] = None
        self.rpc = SimpleRPC()

        @self.rpc.register("draw.line")
        def draw_line(start: Tuple[int, int], end: Tuple[int, int], color: Tuple[int, int, int], width: int = 1) -> None:
            if self._surf:
                pygame.draw.line(self._surf, color, start, end, width)

        @self.rpc.register("ptext.draw")
        def ptext_draw(args: List[Any], kwargs: Dict[str, Any]) -> None:
            if self._surf:
                ptext.draw(*args, surf=self._surf, **kwargs)

        @self.rpc.register("draw.rect")
        def draw_rect(color: Tuple[int, int, int], rect: Tuple[int, int, int, int], width: int = 1) -> None:
            if self._surf:
                pygame.draw.rect(self._surf.surface, color, ZRect(rect), width)

    def set_messages(self, messages: List[JSON]) -> None:
        self._messages = messages

    def draw(self, screen: Screen) -> None:
        self._surf = screen
        self.rpc.dispatch(self._messages)
