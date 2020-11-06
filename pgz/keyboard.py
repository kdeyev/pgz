import re
from typing import Any
from warnings import warn

from pgzero.constants import keys

DEPRECATED_KEY_RE = re.compile(r"[A-Z]")
PREFIX_RE = re.compile(r"^K_(?!\d$)")


class Keyboard:
    """The current state of the keyboard.

    Each attribute represents a key. For example, ::

        keyboard.a

    is True if the 'A' key is depressed, and False otherwise.

    """

    def __init__(self) -> None:

        # The current key state. This may as well be a class attribute - there's
        # only one keyboard.
        self._pressed = set()

    def __getattr__(self, kname: str) -> Any:
        # return is a reserved word, so alias enter to return
        if kname == "enter":
            kname = "return"
        elif DEPRECATED_KEY_RE.match(kname):
            warn("Uppercase keyboard attributes (eg. keyboard.%s) are " "deprecated." % kname, DeprecationWarning, 2)
            kname = PREFIX_RE.sub("", kname)
        try:
            key = keys[kname.upper()]
        except AttributeError:
            raise AttributeError('The key "%s" does not exist' % key)
        return key.value in self._pressed

    def _press(self, key: str) -> None:
        """Called by Game to mark the key as pressed."""
        self._pressed.add(key)

    def _release(self, key: str) -> None:
        """Called by Game to mark the key as released."""
        self._pressed.discard(key)

    def __getitem__(self, k: str) -> Any:
        if isinstance(k, keys):
            return k.value in self._pressed
        else:
            warn("String lookup in keyboard (eg. keyboard[%r]) is " "deprecated." % k, DeprecationWarning, 2)
            return getattr(self, k)

    def __repr__(self) -> str:
        return "<Keyboard pressed={}>".format(self._pressed)


keyboard = Keyboard()
