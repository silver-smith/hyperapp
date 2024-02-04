from collections import defaultdict
from weakref import WeakSet


def _starts_with(sub_path, super_path):
    if len(sub_path) > len(super_path):
        return False
    return super_path[:len(sub_path)] == sub_path


class CommandHub:

    def __init__(self):
        self._path_to_commands = defaultdict(list)
        self._subscribers = set()  # todo: weakref, removed whan 'widget' argument of partial is gone.

    def subscribe(self, fn):
        self._subscribers.add(fn)

    def set_commands(self, path_to_new_commands):
        min_len = min(len(path) for path in path_to_new_commands)
        removed_commands = set()
        for path, command_list in list(self._path_to_commands.items()):
            if len(path) >= min_len:
                del self._path_to_commands[path]
                removed_commands |= set(command_list)
        new_commands = set()
        for path, command_list in path_to_new_commands.items():
            self._path_to_commands[path] += command_list
            new_commands |= set(command_list)
        for fn in self._subscribers:
            fn(removed_commands, new_commands)
