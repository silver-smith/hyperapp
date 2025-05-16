from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import visualizer_fixtures
from .tested.code import construct_default_form


def _sample_form_fn(piece):
    pass


@mark.fixture
def ctx():
    return Context()


@mark.fixture
def adapter_piece():
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_form_fn),
        ctx_params=('piece',),
        service_params=(),
        )
    return htypes.record_adapter.fn_record_adapter(
        record_t=pyobj_creg.actor_to_ref(htypes.construct_default_form_tests.value),
        system_fn=mosaic.put(system_fn),
        )


async def test_construct(visualizer, ctx, adapter_piece):
    piece = await construct_default_form.construct_default_form(
        visualizer, ctx, adapter_piece, htypes.construct_default_form_tests.value)
    assert isinstance(piece, htypes.form.view)
