import abc
from collections import namedtuple


Item = namedtuple('Item', 'name piece_ref widget')


class View(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def construct_widget(self, piece, state, ctx):
        pass

    def get_current(self, piece, widget):
        return 0

    def set_on_current_changed(self, widget, on_changed):
        pass

    def set_on_state_changed(self, piece, widget, on_changed):
        pass

    def set_on_model_state_changed(self, widget, on_changed):
        pass

    def wrapper(self, widget, result):
        return result

    @abc.abstractmethod
    def widget_state(self, piece, widget):
        pass

    def get_commands(self, piece, widget, wrappers):
        return []

    @abc.abstractmethod
    def apply(self, ctx, piece, widget, layout_diff, state_diff):
        pass

    def items(self, piece, widget):
        return []
