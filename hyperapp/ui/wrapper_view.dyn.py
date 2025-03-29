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
        assert idx == 0
        self._ctl_hook.replace_parent_widget(new_child_widget)

    def replace_child(self, ctx, widget, idx, new_child_view, new_child_widget):
        assert idx == 0
        self._base_view = new_child_view
        self.replace_child_widget(widget, idx, new_child_widget)

    def items(self):
        return [Item('base', self._base_view)]

    def item_widget(self, widget, idx):
        assert idx == 0
        return widget
