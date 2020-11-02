from deepdiff import DeepDiff

from .jsonrpc_client import Server
from .rpc import Registrator, serialize_json_array_from_queue, serialize_json_rpc


class RPCScreenServer(Server):
    def __init__(self, size):
        super().__init__()
        self._size = size
        self._prev_messages = []
        self._messages = []

    # def __request(self, method_name, args=None, kwargs=None):
    #     kwargs["_notification"] = Tuple
    #     super().__request(method_name, args, kwargs)

    def send_message(self, message):
        json_message = serialize_json_rpc(message.method, message.params)
        self._messages.append(json_message)

    def _get_messages(self):

        if DeepDiff(self._messages, self._prev_messages) == {}:
            self._messages.clear()
            return False, []
        self._prev_messages = self._messages[:]
        self._messages.clear()
        return True, self._prev_messages[:]


class RPCScreenClient:
    def __init__(self):
        self._messages = []

    def set_messages(self, messages):
        self._messages = messages

    def draw(self, screen):
        for update in self._messages:
            if update["method"] == "draw.text":
                screen.draw.text(**update["params"])
