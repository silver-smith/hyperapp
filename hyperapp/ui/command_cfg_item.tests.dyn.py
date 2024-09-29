from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code import ui_command
from .tested.code import command_cfg_item


def _sample_fn(view, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture
def sample_service():
    return 'a-service'


@mark.fixture.obj
def cfg_item_piece(data_to_ref):
    d = htypes.command_cfg_item_tests.sample_command_d()
    command = htypes.command.ui_command(
        d=data_to_ref(d),
        properties=htypes.command.properties(False, False, False),
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    view_t = htypes.command_cfg_item_tests.view
    return htypes.command.cfg_item(
        t=pyobj_creg.actor_to_ref(view_t),
        command=mosaic.put(command),
        )


def test_construct(cfg_item_piece):
    cfg_item = command_cfg_item.CommandCfgItem.from_piece(cfg_item_piece)
    assert cfg_item.piece == cfg_item_piece


def test_resolve(system, cfg_item_piece):
    cfg_item = command_cfg_item.CommandCfgItem.from_piece(cfg_item_piece)
    command = cfg_item.resolve(system, 'cfg_item_creg')
    assert isinstance(command, ui_command.UnboundUiCommand)
