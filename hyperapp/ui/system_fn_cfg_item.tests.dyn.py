from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.system_fn import ContextFn
from .tested.code import system_fn_cfg_item


def _sample_fn(view, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture
def sample_service():
    return 'a-service'


@mark.fixture
def ctx_fn_piece():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )


@mark.fixture.obj
def cfg_item_piece(ctx_fn_piece):
    return htypes.system_fn.cfg_item(
        t=pyobj_creg.actor_to_ref(htypes.system_fn.ctx_fn),
        system_fn=mosaic.put(ctx_fn_piece),
        )


def test_construct_cfg_item(cfg_item_piece):
    cfg_item = system_fn_cfg_item.SystemFnCfgItem.from_piece(cfg_item_piece)
    assert cfg_item.piece == cfg_item_piece, repr((cfg_item.piece, cfg_item_piece))


def test_resolve_cfg_item(system, cfg_item_piece):
    cfg_item = system_fn_cfg_item.SystemFnCfgItem.from_piece(cfg_item_piece)
    fn = cfg_item.resolve(system, '<unused>')
    assert isinstance(fn, ContextFn)
