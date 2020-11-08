import operator
from typing import Any, Callable, Dict, Optional, Set

import pygame
from pgzero.constants import MUSIC_END, keys, mouse


class EventDispatcher:
    """Adapt a pgzero game's raw handler function to take a Pygame Event.

    Returns a one-argument function of the form ``handler(event)``.
    This will ensure that the correct arguments are passed to the raw
    handler based on its argument spec.

    The wrapped handler will also map certain parameter values using
    callables from EVENT_PARAM_MAPPERS; this ensures that the value of
    'button' inside the handler is a real instance of constants.mouse,
    which means (among other things) that it will print as a symbolic value
    rather than a naive integer.
    """

    EVENT_HANDLERS = {
        pygame.MOUSEBUTTONDOWN: "on_mouse_down",
        pygame.MOUSEBUTTONUP: "on_mouse_up",
        pygame.MOUSEMOTION: "on_mouse_move",
        pygame.KEYDOWN: "on_key_down",
        pygame.KEYUP: "on_key_up",
        MUSIC_END: "on_music_end",
    }

    def map_buttons(val) -> Set[Any]:
        return {c for c, pressed in zip(mouse, val) if pressed}  # type: ignore

    EVENT_PARAM_MAPPERS: Dict[str, Callable] = {"buttons": map_buttons, "button": mouse, "key": keys}

    def load_handlers(self) -> None:
        # from .spellcheck import spellcheck

        # spellcheck(vars(self.mod))
        self.handlers = {}
        for type, name in self.EVENT_HANDLERS.items():
            handler = getattr(self, name, None)
            if callable(handler):
                self.handlers[type] = self.prepare_handler(handler)

    def prepare_handler(self, handler: Callable) -> Callable:

        code = handler.__code__
        param_names = code.co_varnames[: code.co_argcount]

        def make_getter(mapper: Optional[Callable], getter: Callable) -> Callable:
            if mapper:
                event: pygame.event.Event
                return lambda event: mapper(getter(event))  # type: ignore
            return getter

        param_handlers = []
        for name in param_names[1:]:
            getter = operator.attrgetter(name)
            mapper = self.EVENT_PARAM_MAPPERS.get(name)
            param_handlers.append((name, make_getter(mapper, getter)))

        def prep_args(event: pygame.event.Event) -> Dict[str, Any]:
            return {name: get(event) for name, get in param_handlers}

        def new_handler(event: pygame.event.Event) -> Any:
            try:
                prepped = prep_args(event)
            except ValueError:
                # If we couldn't construct the keys/mouse objects representing
                # the button that was pressed, then skip the event handler.
                #
                # This happens because Pygame can generate key codes that it
                # does not have constants for.
                return None
            else:
                return handler(**prepped)

        return new_handler

    def dispatch_event(self, event: pygame.event.Event) -> None:
        handler = self.handlers.get(event.type)
        if handler:
            handler(event)
        else:
            self.handle_event(event)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Override me"""
