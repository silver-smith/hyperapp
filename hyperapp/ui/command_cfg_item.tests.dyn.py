from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code import model_command as model_command_module
from .code import ui_command as ui_command_module
from .tested.code import command_cfg_item


def _sample_fn(view, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture
def sample_service():
    return 'a-service'


@mark.fixture.obj
def cfg_item_piece(data_to_ref):
    d = htypes.command_cfg_item_tests.sample_command_d()
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    command = htypes.command.ui_command(
        d=data_to_ref(d),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(system_fn),
        )
    view_t = htypes.command_cfg_item_tests.view
    return htypes.command.cfg_item(
        t=pyobj_creg.actor_to_ref(view_t),
        command=mosaic.put(command),
        )


@mark.fixture.obj
def ui_command(data_to_ref):
    d = htypes.command_cfg_item_tests.sample_command_d()
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    return htypes.command.ui_command(
        d=data_to_ref(d),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(system_fn),
        )


@mark.fixture.obj
def model_command(data_to_ref):
    d = htypes.command_cfg_item_tests.sample_command_d()
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    return htypes.command.model_command(
        d=data_to_ref(d),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(system_fn),
        )


def test_construct_typed(cfg_item_piece):
    cfg_item = command_cfg_item.TypedCommandCfgItem.from_piece(cfg_item_piece)
    assert cfg_item.piece == cfg_item_piece


def test_construct_untyped_model_command(model_command):
    cfg_item = command_cfg_item.UntypedCommandCfgItem.from_piece(model_command)
    assert cfg_item.piece == model_command


def test_construct_untyped_ui_command(ui_command):
    cfg_item = command_cfg_item.UntypedCommandCfgItem.from_piece(ui_command)
    assert cfg_item.piece == ui_command


def test_resolve_typed(system, cfg_item_piece):
    cfg_item = command_cfg_item.TypedCommandCfgItem.from_piece(cfg_item_piece)
    command = cfg_item.resolve(system, 'cfg_item_creg')
    assert isinstance(command, ui_command_module.UnboundUiCommand)


def test_resolve_untyped_model_command(system, model_command):
    cfg_item = command_cfg_item.UntypedCommandCfgItem.from_piece(model_command)
    command = cfg_item.resolve(system, 'cfg_item_creg')
    assert isinstance(command, model_command_module.UnboundModelCommand)


def test_resolve_untyped_ui_command(system, ui_command):
    cfg_item = command_cfg_item.UntypedCommandCfgItem.from_piece(ui_command)
    command = cfg_item.resolve(system, 'cfg_item_creg')
    assert isinstance(command, ui_command_module.UnboundUiCommand)
