import abc
from collections import namedtuple


Item = namedtuple('Item', 'name view widget')


class View(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def construct_widget(self, state, ctx):
        pass

    def get_current(self, widget):
        return 0

    def set_on_current_changed(self, widget, on_changed):
        pass

    def set_on_state_changed(self, widget, on_changed):
        pass

    def set_on_model_state_changed(self, widget, on_changed):
        pass

    def wrapper(self, widget, result):
        return result

    @abc.abstractmethod
    def widget_state(self, widget):
        pass

    def get_commands(self, widget, wrappers):
        return []

    @abc.abstractmethod
    def apply(self, ctx, widget, layout_diff, state_diff):
        pass

    def items(self, widget):
        return []
