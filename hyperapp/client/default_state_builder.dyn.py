from hyperapp.client.module import ClientModule
from . import htypes


MODULE_NAME = 'default_state_builder'


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.build_default_state = self._build_default_state

    def _build_default_state(self):
        text_object_state = htypes.text_object.text_object('text', 'hello')
        text_handle = htypes.text_object.text_view('text_view', text_object_state)
        navigator_state = htypes.navigator.state(
            view_id='navigator',
            history=[htypes.navigator.item('sample text', text_handle)],
            current_pos=0)
        tabs_state = htypes.tab_view.tab_view_state(tabs=[navigator_state], current_tab=0)
        window_state = htypes.window.window_state(
            tab_view=tabs_state,
            size=htypes.window.size(1000, 800),
            pos=htypes.window.pos(500, 100))
        return [window_state]
