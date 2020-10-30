from .actor import Actor


class MultiplayerActor(Actor):
    def __init__(self, image_name, uuid, deleter):
        super().__init__(image_name)
        self.uuid = uuid
        self.deleter = deleter


class MultiplayerActorStub:
    __slots__ = ("actor", "on_prop_change")

    def __init__(self, actor, on_prop_change):
        self.__class__.actor.__set__(self, actor)
        self.__class__.on_prop_change.__set__(self, on_prop_change)

    def __getattr__(self, name):
        return getattr(self.actor, name)

    def __setattr__(self, name, value):
        setattr(self.actor, name, value)
        getattr(self, "on_prop_change")(self.actor.uuid, name, value)


# class Method(object):
#     def __init__(self, method_name):
#         if method_name.startswith("_"):  # prevent rpc-calls for private methods
#             raise AttributeError("invalid attribute '%s'" % method_name)
#         self.__method_name = method_name

#     def __getattr__(self, method_name):
#         if method_name.startswith("_"):  # prevent rpc-calls for private methods
#             raise AttributeError("invalid attribute '%s'" % method_name)
#         return Method(f"{self.__method_name}.{method_name}")

#     def __call__(self, *args, **kwargs):
#         return rpc.send(self.__method_name, args, kwargs)
