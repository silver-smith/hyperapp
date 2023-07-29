from . import htypes
from .services import (
    mark,
    ui_ctl_creg,
    )


@mark.meta_association(htypes.ui.ctl_association)
def register_ctl_association(ass):
    t = python_object_creg.invite(ass.piece_t)
    ctr_fn = python_object_creg.invite(ass.ctr_fn)
    ui_ctl_creg.register_actor(t, ctr_fn)
