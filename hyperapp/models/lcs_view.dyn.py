from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark


def _dir_to_str(d):
    if isinstance(d, htypes.builtin.record_mt):
        return f'{d.module_name}.{d.name}'
    else:
        return str(d)


@mark.model
def lcs_view(piece, lcs, data_to_ref):
    return [
        htypes.lcs_view.item(
            dir=tuple(data_to_ref(d) for d in dir_set),
            piece=mosaic.put(piece),
            dir_str=", ".join(_dir_to_str(d) for d in dir_set),
            piece_str=str(piece),
            )
        for dir_set, piece in lcs
        ]
        

@mark.global_command
def open_lcs_view():
    return htypes.lcs_view.view()
