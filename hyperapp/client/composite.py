# composite component - base class

import weakref
from . import view


class Composite(view.View):

    def __init__(self, parent, children=None):
        view.View.__init__(self, parent)
        self._children = children or []

    def init(self, module_registry):
        view.View.init(self, module_registry)
        for child in self._children:
            child.init(module_registry)

    def get_command_list(self, kinds=None):
        command_list = super().get_command_list(kinds)
        for child in self._children:
            command_list += child.get_command_list(kinds)
        return command_list
