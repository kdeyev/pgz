from .actor import Actor


class MultiplayerActor(Actor):
    def __init__(self, image_name, uuid, deleter):
        super().__init__(image_name)
        self.uuid = uuid
        self.deleter = deleter


class MultiplayerActorStub:
    def __init__(self, actor):
        self.actor = actor

    # def __getattr__(self, method_name):
    #     name = f"{self.actor.uuid}.{method_name}"
    #     return Method(name)


class Method(object):
    def __init__(self, method_name):
        if method_name.startswith("_"):  # prevent rpc-calls for private methods
            raise AttributeError("invalid attribute '%s'" % method_name)
        self.__method_name = method_name

    def __getattr__(self, method_name):
        if method_name.startswith("_"):  # prevent rpc-calls for private methods
            raise AttributeError("invalid attribute '%s'" % method_name)
        return Method(f"{self.__method_name}.{method_name}")

    def __call__(self, *args, **kwargs):
        return rpc.send(self.__method_name, args, kwargs)
