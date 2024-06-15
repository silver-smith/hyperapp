from .services import (
    mark,
    pyobj_creg,
    )


@mark.service
def data_to_res():
    def _data_to_res(piece):
        return pyobj_creg.actor_to_piece(piece)
    return _data_to_res
