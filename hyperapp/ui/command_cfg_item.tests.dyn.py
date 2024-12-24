from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import command_cfg_item


def _sample_fn(view, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture
def sample_service():
    return 'a-service'


@mark.fixture.obj
def cfg_item_piece():
    d = htypes.command_cfg_item_tests.sample_command_d()
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    command = htypes.command.ui_command(
        d=mosaic.put(d),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(system_fn),
        )
    view_t = htypes.command_cfg_item_tests.view
    return htypes.command.cfg_item(
        t=pyobj_creg.actor_to_ref(view_t),
        command=mosaic.put(command),
        )


def test_typed(cfg_item_piece):
    cfg_item = command_cfg_item.TypedCommandCfgItem.from_piece(cfg_item_piece)
    assert cfg_item.piece == cfg_item_piece


@mark.fixture.obj
def model_command():
    d = htypes.command_cfg_item_tests.sample_command_d()
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    return htypes.command.model_command(
        d=mosaic.put(d),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(system_fn),
        )


def test_untyped_model_command(model_command):
    cfg_item = command_cfg_item.UntypedCommandCfgItem.from_piece(model_command)
    assert cfg_item.piece == model_command


@mark.fixture.obj
def ui_command():
    d = htypes.command_cfg_item_tests.sample_command_d()
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    return htypes.command.ui_command(
        d=mosaic.put(d),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(system_fn),
        )


def test_untyped_ui_command(ui_command):
    cfg_item = command_cfg_item.UntypedCommandCfgItem.from_piece(ui_command)
    assert cfg_item.piece == ui_command
