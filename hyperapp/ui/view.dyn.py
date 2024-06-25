import abc
from collections import namedtuple


Item = namedtuple('Item', 'name view focusable', defaults=[True])


class View(metaclass=abc.ABCMeta):

    def __init__(self):
        self._ctl_hook = None

    def set_controller_hook(self, ctl_hook):
        self._ctl_hook = ctl_hook

    @abc.abstractproperty
    def piece(self):
        pass

    @abc.abstractmethod
    def construct_widget(self, state, ctx):
        pass

    def init_widget(self, widget):
        pass

    def replace_child_widget(self, widget, idx, new_child_widget):
        raise NotImplementedError(self.__class__)

    def get_current(self, widget):
        return None

    def children_context(self, ctx):
        return ctx

    def primary_parent_context(self, rctx, widget):
        return rctx

    def secondary_parent_context(self, rctx, widget):
        return rctx

    async def children_context_changed(self, ctx, rctx, widget):
        pass

    @abc.abstractmethod
    def widget_state(self, widget):
        pass

    def apply(self, ctx, widget, diff):
        raise NotImplementedError()

    def replace_child(self, ctx, widget, idx, new_child_view, new_child_widget):
        pass

    def items(self):
        return []

    def item_widget(self, widget, idx):
        raise RuntimeError(f"Unknown item: {idx}")
