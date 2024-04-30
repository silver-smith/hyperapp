import logging

from . import htypes
from .services import (
    mark,
    mosaic,
    view_creg,
    web,
    )
from .code.auto_tabs import AutoTabsView

log = logging.getLogger(__name__)


@mark.ui_command(htypes.tabs.view)
def move_tab_to_new_group(view, widget, state, ctx):
    group_idx = state.current_tab
    group_widget = view.item_widget(widget, group_idx)
    group_state = web.summon(state.tabs[group_idx])
    group = view.tabs[group_idx].view
    if not isinstance(group, AutoTabsView):
        log.warning(f"Current tab group item is not a auto tabs: {group}")
        return
    if len(group.tabs) < 2:
        log.warning("Current tab group has only one item")
        return
    tab_idx = group.get_current(group_widget)
    tab = group.tabs[tab_idx].view
    tab_state_ref = group_state.tabs[tab_idx]
    new_group_piece = htypes.auto_tabs.view(
        tabs=(mosaic.put(tab.piece),),
        )
    new_group_state = htypes.tabs.state(
        current_tab=0,
        tabs=(tab_state_ref,),
        )
    new_group = view_creg.animate(new_group_piece, ctx)

    group.close_tab(group_widget, tab_idx)
    view.insert_tab(ctx, widget, group_idx + 1, "New group", new_group, new_group_state)
