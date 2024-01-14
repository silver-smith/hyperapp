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

    def set_commands(self, path, new_commands):
        path = tuple(path)
        removed_commands = set()
        for command_path, command_list in list(self._path_to_commands.items()):
            if not _starts_with(command_path, path):
                continue
            removed_commands |= set(command_list)
            del self._path_to_commands[command_path]
        self._path_to_commands[path] += new_commands
        for fn in self._subscribers:
            fn(removed_commands, new_commands)
