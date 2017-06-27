from . import window
from . import tab_view
from . import navigator


def build_default_state(modules):
    view_state_t = modules.text_view.View.get_state_type()
    text_object_state_t = modules.text_object.TextObject.get_state_type()
    text_handle = view_state_t('text_view', text_object_state_t('text', 'hello'))
    navigator_state = navigator.get_state_type()(
        view_id=navigator.View.view_id,
        history=[navigator.get_item_type()('sample text', text_handle)],
        current_pos=0)
    tabs_state = tab_view.get_state_type()(tabs=[navigator_state], current_tab=0)
    window_state = window.get_state_type()(
        tab_view=tabs_state,
        size=window.this_module.size_type(1000, 800),
        pos=window.this_module.point_type(500, 100))
    return [window_state]
