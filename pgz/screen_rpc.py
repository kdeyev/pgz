import pygame
from deepdiff import DeepDiff
from pgzero.rect import RECT_CLASSES, ZRect
from pgzero.screen import make_color, ptext, round_pos

# from .jsonrpc_client import Server
from .rpc import SimpleRPC, serialize_json_message


class RPCSurfacePainter:
    """Interface to pygame.draw that is bound to a surface."""

    def __init__(self, massages):
        self._massages = massages

    def line(self, start, end, color, width=1):
        """Draw a line from start to end."""
        start = round_pos(start)
        end = round_pos(end)

        self._massages.append(serialize_json_message("draw.line", (make_color(color), start, end, width)))
        # pygame.draw.line(self._surf, make_color(color), start, end, width)

    def circle(self, pos, radius, color, width=1):
        """Draw a circle."""
        pos = round_pos(pos)
        self._massages.append(serialize_json_message("draw.circle", (make_color(color), pos, radius, width)))
        # pygame.draw.circle(self._surf, make_color(color), pos, radius, width)

    def filled_circle(self, pos, radius, color):
        """Draw a filled circle."""
        pos = round_pos(pos)
        self._massages.append(serialize_json_message("draw.circle", (make_color(color), pos, radius, 0)))
        # pygame.draw.circle(self._surf, make_color(color), pos, radius, 0)

    def polygon(self, points, color):
        """Draw a polygon."""
        try:
            iter(points)
        except TypeError:
            raise TypeError("screen.draw.filled_polygon() requires an iterable of points to draw") from None  # noqa
        points = [round_pos(point) for point in points]
        self._massages.append(serialize_json_message("draw.polygon", (make_color(color), points, 1)))
        # pygame.draw.polygon(self._surf, make_color(color), points, 1)

    def filled_polygon(self, points, color):
        """Draw a filled polygon."""
        try:
            iter(points)
        except TypeError:
            raise TypeError("screen.draw.filled_polygon() requires an iterable of points to draw") from None  # noqa
        points = [round_pos(point) for point in points]
        self._massages.append(serialize_json_message("draw.polygon", (make_color(color), points, 0)))
        # pygame.draw.polygon(self._surf, make_color(color), points, 0)

    def rect(self, rect, color, width=1):
        """Draw a rectangle."""
        if not isinstance(rect, RECT_CLASSES):
            raise TypeError("screen.draw.rect() requires a rect to draw")
        self._massages.append(serialize_json_message("draw.rect", make_color(color), (rect.x, rect.y, rect.w, rect.h), width))
        # pygame.draw.rect(self._surf, make_color(color), rect, width)

    def filled_rect(self, rect, color):
        """Draw a filled rectangle."""
        if not isinstance(rect, RECT_CLASSES):
            raise TypeError("screen.draw.filled_rect() requires a rect to draw")
        self._massages.append(serialize_json_message("draw.rect", make_color(color), (rect.x, rect.y, rect.w, rect.h), 0))
        # pygame.draw.rect(self._surf, make_color(color), rect, 0)

    def text(self, *args, **kwargs):
        """Draw text to the screen."""
        # FIXME: expose ptext parameters, for autocompletion and autodoc
        self._massages.append(serialize_json_message("ptext.draw", args=args, kwargs=kwargs))
        # ptext.draw(*args, surf=self._surf, **kwargs)

    def textbox(self, *args, **kwargs):
        """Draw text to the screen, wrapped to fit a box"""
        # FIXME: expose ptext parameters, for autocompletion and autodoc
        self._massages.append(serialize_json_message("ptext.drawbox", args=args, kwargs=kwargs))
        # ptext.drawbox(*args, surf=self._surf, **kwargs)


class RPCScreenServer:
    def __init__(self, size):
        super().__init__()
        self._size = size
        self._prev_messages = []
        self._messages = []

        self.width, self.height = size

    # def send_message(self, message):
    #     json_message = serialize_json_message(message.method, message.params)
    #     self._messages.append(json_message)

    def get_messages(self):
        if DeepDiff(self._messages, self._prev_messages) == {}:
            self._messages.clear()
            return False, []
        self._prev_messages = self._messages[:]
        self._messages.clear()
        return True, self._prev_messages[:]

    def bounds(self):
        """Return a Rect representing the bounds of the screen."""
        return ZRect((0, 0), (self.width, self.height))

    def clear(self):
        """Clear the screen to black."""
        self._massages.append(serialize_json_message("fill", (0, 0, 0)))
        # self.fill((0, 0, 0))

    def fill(self, color, gcolor=None):
        self._massages.append(serialize_json_message("fill", (color, gcolor)))

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

    def blit(self, image, pos):
        self._massages.append(serialize_json_message("blit", (image, pos)))
        # if isinstance(image, str):
        #     image = loaders.images.load(image)
        # self.surface.blit(image, pos)

    @property
    def draw(self):
        return RPCSurfacePainter(self._messages)

    def __repr__(self):
        return "<RPCScreenServer width={} height={}>".format(self.width, self.height)


class RPCScreenClient:
    def __init__(self):
        self._messages = []
        self._surf = None
        self.rpc = SimpleRPC()

        @self.rpc.register("draw.line")
        def draw_line(start, end, color, width=1):
            pygame.draw.line(self._surf, color, start, end, width)

        @self.rpc.register("ptext.draw")
        def ptext_draw(args, kwargs):
            ptext.draw(*args, surf=self._surf, **kwargs)

        @self.rpc.register("draw.rect")
        def draw_rect(color, rect, width=1):
            pygame.draw.rect(self._surf.surface, color, ZRect(rect), width)

    def set_messages(self, messages):
        self._messages = messages

    def draw(self, screen):
        self._surf = screen
        self.rpc.dispatch(self._messages)
