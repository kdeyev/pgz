import asyncio
import json
from functools import wraps
from typing import Any, Callable, Optional, Tuple

import websockets

from .json_rpc import Registrator


def serialize_json_rpc(method_name, args=None, kwargs=None, is_notification=True):
    """Generate the raw JSON message to be sent to the server"""
    data = {"jsonrpc": "2.0", "method": method_name}

    if args and kwargs:
        raise Exception("JSON-RPC spec forbids mixing arguments and keyword arguments")

    import collections

    # from the specs:
    # "If resent, parameters for the rpc call MUST be provided as a Structured value.
    #  Either by-position through an Array or by-name through an Object."
    if args and len(args) == 1 and isinstance(args[0], collections.Mapping):
        args = dict(args[0])

    is_notification = True
    params = args or kwargs

    if params:
        data["params"] = params
    if not is_notification:
        import random
        import sys

        # some JSON-RPC servers complain when receiving str(uuid.uuid4()). Let's pick something simpler.
        data["id"] = random.randint(1, sys.maxsize)
    # return json.dumps(data)
    return data


# class RPC:
#     def __init__(self, url: Optional[str] = None) -> None:

#         self._loop = asyncio.get_event_loop()
#         self.registrator = Registrator(self._loop)

#     def register(self, name: str, func):
#         self.registrator._set_rpc(name, func)

#     def handle_message(self, message):
#         self.registrator.dispatch(message)


def _auto_rpc(func: Callable, method_name: str) -> Callable:
    @wraps(func)
    def auto_rpc_decorated(*args: Any, **kwargs: Any) -> Any:
        if rpc.client:
            rpc.send(method_name, args, kwargs)
        else:
            return func(*args, **kwargs)

    return auto_rpc_decorated


def auto_rpc_class_methods(Cls: Any) -> Any:
    rpc_name: str = "aas"

    class AutoRPCCls(object):
        def __init__(self, *args: Any, **kwargs: Any):
            instance = Cls(*args, **kwargs)
            for attr, value in instance.__dict__.items():
                if attr.startswith("_"):
                    continue
                if callable(value):
                    name = f"{rpc_name}.{attr}"
                    rpc.register(name, value)

            self._instance = instance

        def __getattribute__(self, s: Any) -> Any:
            """
            this is called whenever any attribute of a NewCls object is accessed. This function first tries to
            get the attribute off NewCls. If it fails then it tries to fetch the attribute from self.oInstance (an
            instance of the decorated class). If it manages to fetch the attribute from self.oInstance, and
            the attribute is an instance method then `time_this` is applied.
            """
            try:
                x = super(AutoRPCCls, self).__getattribute__(s)
            except AttributeError:
                pass
            else:
                return x
            x = self._instance.__getattribute__(s)
            if type(x) == type(self.__init__):  # type: ignore # it is an instance method # noqa: E721
                name = f"{rpc_name}.{x.__name__}"
                return _auto_rpc(x, name)
            else:
                return x

        def __setattr__(self, attr, value):
            if attr == "_instance":
                return object.__setattr__(self, attr, value)
            if rpc.client:
                name = f"{rpc_name}.__setattr__"
                kwargs = {attr: attr}
                rpc.send(name, kwargs=kwargs)
            else:
                return object.__setattr__(self, attr, value)

    return AutoRPCCls
