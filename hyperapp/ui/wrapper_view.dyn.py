from .code.view import View


class WrapperView(View):

    def __init__(self, base_view):
        super().__init__()
        self._base = base_view

    def set_controller_hook(self, ctl_hook):
        super().set_controller_hook(ctl_hook)
        self._base.set_controller_hook(ctl_hook)

    def construct_widget(self, state, ctx):
        return self._base.construct_widget(state, ctx)

    def replace_widget(self, ctx, widget, idx):
        self._base.replace_widget(ctx, widget, idx)

    def get_current(self, widget):
        return self._base.get_current(widget)

    def widget_state(self, widget):
        return self._base.widget_state(widget)

    def apply(self, ctx, widget, diff):
        return self._base.apply(ctx, widget, diff)

    def items(self):
        return self._base.items()

    def item_widget(self, widget, idx):
        return self._base.item_widget(widget, idx)
