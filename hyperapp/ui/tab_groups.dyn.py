import logging

from . import htypes
from .services import (
    mark,
    mosaic,
    web,
    )
from .code.list_diff import ListDiff
from .code.view import Diff

log = logging.getLogger(__name__)


@mark.ui_command(htypes.tabs.view)
def move_tab_to_new_group(piece, state):
    group_idx = state.current_tab
    group_state = web.summon(state.tabs[group_idx])
    group = web.summon(piece.tabs[group_idx].ctl)
    if not isinstance(group, htypes.auto_tabs.view):
        log.warning(f"Current tab group item is not a auto tabs: {group}")
        return
    if len(group.tabs) < 2:
        log.warning("Current tab group has only one item")
        return
    tab_idx = group_state.current_tab
    tab_ref = group.tabs[tab_idx]
    modify_group_diff = Diff(
        piece=ListDiff.Modify(
            idx=group_idx,
            item_diff=ListDiff.Remove(idx=tab_idx),
            ),
        state=ListDiff.Modify(
            idx=group_idx,
            item_diff=ListDiff.Remove(idx=tab_idx),
            ),
        )
    new_tabs = htypes.auto_tabs.view((tab_ref,))
    new_group_tab = htypes.tabs.tab("New group", mosaic.put(new_tabs))
    new_group_tab_state = htypes.tabs.state(
        current_tab=0,
        tabs=(group_state.tabs[tab_idx],),
        )
    insert_diff = Diff(
        ListDiff.Insert(group_idx + 1, new_group_tab),
        ListDiff.Insert(group_idx + 1, mosaic.put(new_group_tab_state)),
        )
    return [modify_group_diff, insert_diff]
