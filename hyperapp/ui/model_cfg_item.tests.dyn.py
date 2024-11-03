from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import model_cfg_item


def _sample_fn(view, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture.obj
def model():
    ui_t = htypes.model.list_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.model_cfg_item_tests.item),
        )
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    return htypes.model.model(
        ui_t=mosaic.put(ui_t),
        system_fn=mosaic.put(system_fn),
        )


@mark.fixture.obj
def piece(model):
    return htypes.model.cfg_item(
        t=pyobj_creg.actor_to_ref(htypes.model_cfg_item_tests.model),
        model=mosaic.put(model),
        )


def test_construct(piece):
    cfg_item = model_cfg_item.ModelCfgItem.from_piece(piece)
    assert cfg_item.piece == piece


def test_resolve(system, model, piece):
    cfg_item = model_cfg_item.ModelCfgItem.from_piece(piece)
    resolved_model = cfg_item.resolve(system, '<unused>')
    assert resolved_model == model
