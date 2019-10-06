from hyperapp.common.ref import phony_ref
from hyperapp.client.module import ClientModule
from . import htypes


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._ref_registry = services.ref_registry
        services.default_state_builder = self._build_default_state

    def _build_default_state(self):
        tab_view = htypes.tab_view.tab_view([], 0)
        tab_view_ref = self._ref_registry.register_object(tab_view)
        window_state = htypes.window.window(
            central_view_ref=tab_view_ref,
            size=htypes.window.size(1000, 800),
            pos=htypes.window.pos(500, 100))
        return [window_state]

    # def _build_default_state(self):
    #     text_object_state = htypes.text.text('text', 'hello')
    #     text_handle = htypes.text.text_view('text_view', text_object_state)
    #     navigator_state = htypes.navigator.state(
    #         view_id='navigator',
    #         history=[htypes.navigator.item('sample text', text_handle)],
    #         current_pos=0)
    #     tabs_state = htypes.tab_view.tab_view(tabs=[navigator_state], current_tab=0)
    #     window_state = htypes.window.window(
    #         tab_view=tabs_state,
    #         size=htypes.window.size(1000, 800),
    #         pos=htypes.window.pos(500, 100))
    #     return [window_state]
