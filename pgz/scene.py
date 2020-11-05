import operator

import pygame
from pgzero.constants import MUSIC_END, keys, mouse


class EventDispatcher:

    EVENT_HANDLERS = {
        pygame.MOUSEBUTTONDOWN: "on_mouse_down",
        pygame.MOUSEBUTTONUP: "on_mouse_up",
        pygame.MOUSEMOTION: "on_mouse_move",
        pygame.KEYDOWN: "on_key_down",
        pygame.KEYUP: "on_key_up",
        MUSIC_END: "on_music_end",
    }

    def map_buttons(val):
        return {c for c, pressed in zip(mouse, val) if pressed}

    EVENT_PARAM_MAPPERS = {"buttons": map_buttons, "button": mouse, "key": keys}

    def load_handlers(self):
        # from .spellcheck import spellcheck

        # spellcheck(vars(self.mod))
        self.handlers = {}
        for type, name in self.EVENT_HANDLERS.items():
            handler = getattr(self, name, None)
            if callable(handler):
                self.handlers[type] = self.prepare_handler(handler)

    def prepare_handler(self, handler):
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
        code = handler.__code__
        param_names = code.co_varnames[: code.co_argcount]

        def make_getter(mapper, getter):
            if mapper:
                return lambda event: mapper(getter(event))
            return getter

        param_handlers = []
        for name in param_names[1:]:
            getter = operator.attrgetter(name)
            mapper = self.EVENT_PARAM_MAPPERS.get(name)
            param_handlers.append((name, make_getter(mapper, getter)))

        def prep_args(event):
            return {name: get(event) for name, get in param_handlers}

        def new_handler(event):
            try:
                prepped = prep_args(event)
            except ValueError:
                # If we couldn't construct the keys/mouse objects representing
                # the button that was pressed, then skip the event handler.
                #
                # This happens because Pygame can generate key codes that it
                # does not have constants for.
                return
            else:
                return handler(**prepped)

        return new_handler

    def dispatch_event(self, event):
        handler = self.handlers.get(event.type)
        if handler:
            handler(event)
            return True
        else:
            self.handle_event(event)


class Scene(EventDispatcher):
    """
    The idea and the original code was taken from EzPyGame:
    https://github.com/Mahi/EzPyGame


    An isolated scene which can be ran by an application.

    Create your own scene by subclassing and overriding any methods.
    The hosting :class:`.Application` instance is accessible
    through the :attr:`application` property.

    Example usage with two scenes interacting:

    .. code-block:: python

        class Menu(Scene):

            def __init__(self):
                self.font = pygame.font.Font(...)

            def on_enter(self, previous_scene):
                self.application.title = 'Main Menu'
                self.application.resolution = (640, 480)
                self.application.update_rate = 30

            def draw(self, screen):
                pygame.draw.rect(...)
                text = self.font.render(...)
                screen.blit(text, ...)

            def handle_event(self, event):
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        game_size = self._get_game_size(event.pos)
                        self.change_scene(Game(game_size))

            def _get_game_size(self, mouse_pos_upon_click):
                ...


        class Game(ezpygame.Scene):
            title = 'The Game!'
            resolution = (1280, 720)
            update_rate = 60

            def __init__(self, size):
                super().__init__()
                self.size = size
                self.player = ...
                ...

            def on_enter(self, previous_scene):
                super().on_enter(previous_scene)
                self.previous_scene = previous_scene

            def draw(self, screen):
                self.player.draw(screen)
                for enemy in self.enemies:
                    ...

            def update(self, dt):
                self.player.move(dt)
                ...
                if self.player.is_dead():
                    self.application.change_scene(self.previous_scene)
                elif self.player_won():
                    self.application.change_scene(...)

            def handle_event(self, event):
                ...  # Player movement etc.

    The above two classes use different approaches for changing
    the application's settings when the scene is entered:

    1. Manually set them in :meth:`on_enter`, as seen in ``Menu``
    2. Use class variables, as I did with ``Game``

    When using class variables (2), you can leave out any setting
    (defaults to ``None``) to not override that particular setting.
    If you override :meth:`on_enter` in the subclass, you must call
    ``super().on_enter(previous_scene)`` to use the class variables.

    These settings can further be overridden in individual instances:

    .. code-block:: python

        my_scene0 = MyScene()
        my_scene0.resolution = (1280, 720)
        my_scene1 = MyScene(title='My Second Awesome Scene')
    """

    # title = None
    # resolution = None
    # update_rate = None

    # def __init__(self, title=None, resolution=None, update_rate=None):
    #     self._application = None
    #     if title is not None:
    #         self.title = title
    #     if resolution is not None:
    #         self.resolution = resolution
    #     if update_rate is not None:
    #         self.update_rate = update_rate

    @property
    def application(self):
        """The host application that's currently running the scene."""
        return self._application

    @property
    def screen(self):
        return self.application.screen

    @property
    def resolution(self):
        return self.application.resolution

    @property
    def clock(self):
        return self.application.clock

    def draw(self, screen):
        """Override this with the scene drawing.

        :param pygame.Surface screen: screen to draw the scene on
        """

    def update(self, dt):
        """Override this with the scene update tick.

        :param int dt: time in milliseconds since the last update
        """

    def handle_event(self, event):
        """Override this to handle an event in the scene.

        All of :mod:`pygame`'s events are sent here, so filtering
        should be applied manually in the subclass.

        :param pygame.event.Event event: event to handle
        """

    def on_enter(self, previous_scene):
        """Override this to initialize upon scene entering.

        The :attr:`application` property is initialized at this point,
        so you are free to access it through ``self.application``.
        Stuff like changing resolution etc. should be done here.

        If you override this method and want to use class variables
        to change the application's settings, you must call
        ``super().on_enter(previous_scene)`` in the subclass.

        :param Scene|None previous_scene: previous scene to run
        """
        # for attr in ("title", "resolution", "update_rate"):
        #     value = getattr(self, attr)
        #     if value is not None:
        #         setattr(self.application, attr.lower(), value)

        self.load_handlers()

    def on_exit(self, next_scene):
        """Override this to deinitialize upon scene exiting.

        The :attr:`application` property is still initialized at this
        point. Feel free to do saving, settings reset, etc. here.

        :param Scene|None next_scene: next scene to run
        """
