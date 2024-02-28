import logging

from . import htypes
from .services import (
    ui_ctl_creg,
    )
from .code.list_diff import ListDiff
from .code.wrapper_view import WrapperView

log = logging.getLogger(__name__)


class TabGroupsView(WrapperView):

    @classmethod
    def from_piece(cls, piece):
        base_piece = htypes.tabs.layout(piece.tabs)
        base = ui_ctl_creg.animate(base_piece)
        return cls(base)

    @property
    def piece(self):
        return htypes.tab_groups.view(self._base.piece.tabs)

    def apply(self, ctx, widget, layout_diff, state_diff):
        log.info("TabGroups: apply: %s / %s", layout_diff, state_diff)
        if isinstance(layout_diff, (ListDiff.Insert, ListDiff.Modify, ListDiff.Remove)):
            return self._base.apply(ctx, widget, layout_diff, state_diff)
        else:
            raise NotImplementedError(f"Not implemented: tab_groups.apply({layout_diff})")
