from collections import defaultdict

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.lcs_view import dir_to_str


@mark.model
def lcs_dirs_view(piece, lcs):
    d_to_count = defaultdict(int)
    for layer_d, dir_set, piece in lcs:
        for d in dir_set:
            d_to_count[d] += 1
    return [
        htypes.lcs_dirs_view.item(
            d=mosaic.put(d),
            d_str=dir_to_str(d),
            item_count=count
            )
        for d, count in sorted(
                d_to_count.items(),
                key=lambda i: -i[1],
                )
        ]


@mark.command
def lcs_dirs_items(piece, current_item):
    return htypes.lcs_view.view(
        filter=(current_item.d,),
        )


@mark.command
def lcs_open_dirs(piece):
    return htypes.lcs_dirs_view.view()
