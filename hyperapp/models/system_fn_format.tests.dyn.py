from . import htypes
from .services import (
    pyobj_creg,
    )
from .tested.code import system_fn_format


def _sample_fn():
    pass


def test_ctx_fn():
    piece = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=(),
        service_params=(),
        )
    title = system_fn_format.format_ctx_fn(piece)
    assert type(title) is str
