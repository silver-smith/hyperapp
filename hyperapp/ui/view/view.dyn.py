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

    def init_widget(self, widget, focusable):
        pass

    def replace_child_widget(self, widget, idx, new_child_widget):
        raise NotImplementedError(self.__class__)

    def get_current(self, widget):
        return None

    def me_or_child_has_focus(self, widget):
        if widget.hasFocus():
            return True
        idx = self.get_current(widget)
        if idx is None:
            return False
        item_view = self.items()[idx].view
        item_widget = self.item_widget(widget, idx)
        return item_view.me_or_child_has_focus(item_widget)

    def children_context(self, ctx):
        return ctx

    def primary_parent_context(self, rctx, widget):
        return rctx

    def secondary_parent_context(self, rctx, widget):
        return rctx

    async def children_changed(self, ctx, rctx, widget, save_layout):
        pass

    def make_widget_state(self, key):
        return None

    def set_current_key(self, widget, key):
        pass

    @abc.abstractmethod
    def widget_state(self, widget):
        pass

    def replace_child(self, ctx, widget, idx, new_child_view, new_child_widget):
        pass

    def items(self):
        return []

    def item_widget(self, widget, idx):
        raise RuntimeError(f"Unknown item: {idx}")
