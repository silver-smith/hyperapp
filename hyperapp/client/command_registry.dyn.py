import weakref


class CommandRegistry:

    def __init__(self):
        self._observer_set = weakref.WeakSet()

    def subscribe(self, observer):
        self._observer_set.add(observer)

    def unsubscribe(self, observer):
        self._observer_set.remove(observer)

    def set_commands(self, kind, command_list):
        for observer in self._observer_set:
            observers.set_commands(kind, command_list)
