# composite component - base class

import weakref
from . import view


class Composite(view.View):

    def __init__(self, parent, children):
        view.View.__init__(self, parent)
        self._children = children

    def init(self, module_registry):
        view.View.init(self, module_registry)
        for child in self._children:
            child.init(module_registry)
