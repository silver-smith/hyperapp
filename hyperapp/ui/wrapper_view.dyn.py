from .code.view import Item, View


class WrapperView(View):

    def __init__(self, base_view):
        super().__init__()
        self._base_view = base_view

    def construct_widget(self, state, ctx):
        return self._base_view.construct_widget(state, ctx)

    def widget_state(self, widget):
        return self._base_view.widget_state(widget)

    def get_current(self, widget):
        return 0

    def replace_child_widget(self, widget, idx, new_child_widget):
        self._base_view.replace_child_widget(widget, idx, new_child_widget)

    def items(self):
        return [Item('base', self._base_view)]

    def item_widget(self, widget, idx):
        return self._base_view.item_widget(widget, idx)
