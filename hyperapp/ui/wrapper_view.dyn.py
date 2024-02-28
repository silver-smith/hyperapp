from .code.view import View


class WrapperView(View):

    def __init__(self, base_view):
        super().__init__()
        self._base = base_view

    def construct_widget(self, state, ctx):
        return self._base.construct_widget(state, ctx)

    def get_current(self, widget):
        return self._base.get_current(widget)

    def set_on_item_changed(self, on_changed):
        self._base.set_on_item_changed(on_changed)

    def set_on_child_changed(self, on_changed):
        self._base.set_on_child_changed(on_changed)

    def set_on_current_changed(self, widget, on_changed):
        self._base.set_on_current_changed(widget, on_changed)

    def wrapper(self, widget, diffs):
        return self._base.wrapper(widget, diffs)

    def widget_state(self, widget):
        return self._base.widget_state(widget)

    def apply(self, ctx, widget, layout_diff, state_diff):
        return self._base.apply(ctx, widget, layout_diff, state_diff)

    def items(self, widget):
      return self._base.items(widget)
