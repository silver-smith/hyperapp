from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.system_fn import ContextFn
from .tested.code import view_cfg_item


def _sample_fn(view, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture
def sample_service():
    return 'a-service'


@mark.fixture.obj
def cfg_item_piece():
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    t = htypes.view_cfg_item_tests.sample_view
    return htypes.view.view_template(
        t=pyobj_creg.actor_to_ref(t),
        system_fn=mosaic.put(system_fn),
        )


def test_cfg_item(system, cfg_item_piece):
    cfg_item = view_cfg_item.ViewCfgItem.from_piece(cfg_item_piece)
    fn = cfg_item.resolve(system, "<unused service name>")
    assert isinstance(fn, ContextFn)
