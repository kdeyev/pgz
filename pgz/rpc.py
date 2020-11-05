import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

JSON = Dict[str, Any]


class SimpleRPC:
    def __init__(self) -> None:
        self._functions: Dict[str, Callable] = {}

    def _set_rpc(self, name, func):
        self._functions[name] = func
        return func

    def register(self, target: Callable):
        if isinstance(target, str):

            # call as decorator with argument
            def decorate(func):
                return self._set_rpc(target, func)

            return decorate

        else:
            # call as normal decorator
            func = target
            return self._set_rpc(func.__name__, func)

    def __call__(self, request):
        return self.register(request)

    def dispatch(self, request: Union[JSON, List[JSON]]):
        if isinstance(request, List):
            for r in request:
                self._dispatch(r)
        else:
            return self._dispatch(request)

    def _dispatch(self, request: JSON):
        method = request["method"]
        args = request["args"]
        kwargs = request["kwargs"]
        func = self._functions[method]
        func(*args, **kwargs)


def serialize_json_message(method_name: str, *args, **kwarg) -> JSON:
    return {"method": method_name, "args": args, "kwargs": kwarg}


def serialize_json_array_from_queue(queue) -> str:
    json_messages: List[JSON] = []
    try:
        # Run until exception
        while True:
            json_messages.append(queue.get_nowait())
    except asyncio.QueueEmpty as e:
        pass

    # create one json array
    message = json.dumps(json_messages)
    return message


# # class RPC:
# #     def __init__(self, url: Optional[str] = None) -> None:

# #         self._loop = asyncio.get_event_loop()
# #         self.registrator = Registrator(self._loop)

# #     def register(self, name: str, func):
# #         self.registrator._set_rpc(name, func)

# #     def handle_message(self, message):
# #         self.registrator.dispatch(message)


# def _auto_rpc(func: Callable, method_name: str) -> Callable:
#     @wraps(func)
#     def auto_rpc_decorated(*args: Any, **kwargs: Any) -> Any:
#         if rpc.client:
#             rpc.send(method_name, args, kwargs)
#         else:
#             return func(*args, **kwargs)

#     return auto_rpc_decorated


# def auto_rpc_class_methods(Cls: Any) -> Any:
#     rpc_name: str = "aas"

#     class AutoRPCCls(object):
#         def __init__(self, *args: Any, **kwargs: Any):
#             instance = Cls(*args, **kwargs)
#             for attr, value in instance.__dict__.items():
#                 if attr.startswith("_"):
#                     continue
#                 if callable(value):
#                     name = f"{rpc_name}.{attr}"
#                     rpc.register(name, value)

#             self._instance = instance

#         def __getattribute__(self, s: Any) -> Any:
#             """
#             this is called whenever any attribute of a NewCls object is accessed. This function first tries to
#             get the attribute off NewCls. If it fails then it tries to fetch the attribute from self.oInstance (an
#             instance of the decorated class). If it manages to fetch the attribute from self.oInstance, and
#             the attribute is an instance method then `time_this` is applied.
#             """
#             try:
#                 x = super(AutoRPCCls, self).__getattribute__(s)
#             except AttributeError:
#                 pass
#             else:
#                 return x
#             x = self._instance.__getattribute__(s)
#             if type(x) == type(self.__init__):  # type: ignore # it is an instance method # noqa: E721
#                 name = f"{rpc_name}.{x.__name__}"
#                 return _auto_rpc(x, name)
#             else:
#                 return x

#         def __setattr__(self, attr, value):
#             if attr == "_instance":
#                 return object.__setattr__(self, attr, value)
#             if rpc.client:
#                 name = f"{rpc_name}.__setattr__"
#                 kwargs = {attr: attr}
#                 rpc.send(name, kwargs=kwargs)
#             else:
#                 return object.__setattr__(self, attr, value)

#     return AutoRPCCls
