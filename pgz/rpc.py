from functools import wraps
from typing import Any, Callable, Optional

from .json_rpc import Registrator
from .json_rpc_client import Server


class RPC:
    def __init__(self, url: Optional[str] = None) -> None:
        self.client = None
        if url:
            self.client = Server(url)

        self.registrator = Registrator()

    def register(self, name: str, func):
        self.registrator._set_rpc(name, func)

    def send(self, method_name, args=None, kwargs=None):
        self.client.__request(method_name, args, kwargs)


rpc = RPC()


def _auto_rpc(method_name: str, func: Callable) -> Callable:
    rpc.register(method_name, func)

    @wraps(func)
    def auto_rpc_decorated(*args: Any, **kwargs: Any) -> Any:
        if rpc.client:
            rpc.send(method_name, args, kwargs)
        else:
            return func(*args, **kwargs)

    return auto_rpc_decorated


def auto_rpc_class_methods(Cls: Any) -> Any:
    class AutoLockCls(object):
        def __init__(self, *args: Any, rpc_name: str, **kwargs: Any):
            self.client = True
            self._instance = Cls(*args, **kwargs)

        def __getattribute__(self, s: Any) -> Any:
            """
            this is called whenever any attribute of a NewCls object is accessed. This function first tries to
            get the attribute off NewCls. If it fails then it tries to fetch the attribute from self.oInstance (an
            instance of the decorated class). If it manages to fetch the attribute from self.oInstance, and
            the attribute is an instance method then `time_this` is applied.
            """
            try:
                x = super(AutoLockCls, self).__getattribute__(s)
            except AttributeError:
                pass
            else:
                return x
            x = self.oInstance.__getattribute__(s)
            if type(x) == type(self.__init__):  # type: ignore # it is an instance method # noqa: E721
                return _auto_rpc(x, self.client)
            else:
                return x

    return AutoLockCls
