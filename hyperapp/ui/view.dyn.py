import abc
from collections import namedtuple


Item = namedtuple('Item', 'name view widget')
Diff = namedtuple('Diff', 'piece state', defaults=[None])


class View(metaclass=abc.ABCMeta):

    @abc.abstractproperty
    def piece(self):
        pass

    @abc.abstractmethod
    def construct_widget(self, state, ctx):
        pass

    def replace_widget(self, ctx, widget, idx):
        pass

    def get_current(self, widget):
        return 0

    def child_state_changed(self, widget):
        pass

    def set_on_commands_changed(self, on_changed):
        pass

    def set_on_item_changed(self, on_changed):
        pass

    def set_on_child_changed(self, on_changed):
        pass

    def set_on_current_changed(self, widget, on_changed):
        pass

    def set_on_state_changed(self, widget, on_changed):
        pass

    @abc.abstractmethod
    def widget_state(self, widget):
        pass

    def get_commands(self, widget, wrappers):
        return []

    def apply(self, ctx, widget, diff):
        raise NotImplementedError()

    def items(self, widget):
        return []
