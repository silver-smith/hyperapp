# composite component - base class

import weakref

from . import view


class Composite(view.View):

    def __init__(self, parent=None, children=None):
        view.View.__init__(self)
        self._children = children or []

    def get_command_list(self):
        command_list = super().get_command_list()
        for child in self._children:
            command_list += child.get_command_list()
        return command_list
