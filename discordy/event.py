import inspect
import asyncio
import collections


class Manager:
    __slots__ = "client"

    def __init__(self, client):
        self.client = client

    def get_listeners(self):
        listeners = set()

        for name, member in inspect.getmembers(self):
            if not name.startswith("on_"):
                continue

            if not inspect.ismethod(member) and \
                not inspect.iscoroutinefunction(member):
                    raise TypeError("coroutine method expected")

            listeners.add(member)

        return listeners


class Handler:
    __slots__ = "listeners"

    def __init__(self, managers):
        self.listeners = collections.defaultdict(list)

        for manager in managers:
            for listener in manager.get_listeners():
                name = listener.__name__[3:]
                self.listeners[name].append(listener)

    def emit(self, event, *args, **kwargs):
        listeners = self.listeners[event]

        for listener in listeners:
            coro = listener(*args, **kwargs)
            asyncio.ensure_future(coro)
