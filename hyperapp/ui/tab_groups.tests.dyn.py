from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import tab_groups


def test_move_tab_to_new_group():
    adapter_piece = htypes.str_adapter.static_str_adapter("Sample text")
    text_piece = htypes.text.readonly_view(mosaic.put(adapter_piece))
    inner_tabs_piece = htypes.auto_tabs.view(
        tabs=(
            mosaic.put(text_piece),
            mosaic.put(text_piece),
            ),
        )
    outer_tabs_piece = htypes.tabs.view(
        tabs=(
            htypes.tabs.tab("Outer", mosaic.put(inner_tabs_piece)),
            ),
        )
    text_state = htypes.text.state()
    inner_tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(
            mosaic.put(text_state),
            mosaic.put(text_state),
            ),
        )
    outer_tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(inner_tabs_state),),
        )

    tab_groups.move_tab_to_new_group(outer_tabs_piece, outer_tabs_state)
