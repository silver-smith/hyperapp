from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.model_command import UnboundGlobalModelCommand
from .code.ui_command import UnboundUiCommand
from .code.args_picker_command_enum import UnboundArgsPickerCommandEnumerator
from .tested.code import command_cfg_item


def _sample_fn(view, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture
def sample_service():
    return 'a-service'


@mark.fixture.obj
def command_template():
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
    return htypes.command.command_template(
        command=mosaic.put(command),
        )


def test_typed(system, command_template):
    command = command_cfg_item.resolve_typed_command_cfg_value(
        command_template, '<unused-key>', system, '<unused-service-name>')
    assert isinstance(command, UnboundUiCommand)


@mark.fixture.obj
def global_model_command():
    d = htypes.command_cfg_item_tests.sample_command_d()
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    return htypes.command.global_model_command(
        d=mosaic.put(d),
        properties=htypes.command.properties(False, False, False),
        system_fn=mosaic.put(system_fn),
        preserve_remote=False,
        )


def test_untyped_model_command(system, global_model_command):
    key, piece = command_cfg_item.resolve_untyped_command_cfg_item(global_model_command)
    assert key is None
    assert piece == global_model_command
    command = command_cfg_item.resolve_untyped_command_cfg_value(global_model_command, key, system, '<unused-service-name>')
    assert isinstance(command, UnboundGlobalModelCommand)


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


def test_untyped_ui_command(system, ui_command):
    key, piece = command_cfg_item.resolve_untyped_command_cfg_item(ui_command)
    assert key is None
    assert piece == ui_command
    command = command_cfg_item.resolve_untyped_command_cfg_value(ui_command, key, system, '<unused-service-name>')
    assert isinstance(command, UnboundUiCommand)


@mark.fixture
def args_picker_enum(enum_t):
    d = htypes.command_cfg_item_tests.sample_command_d()
    fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )
    return enum_t(
        name='sample-command',
        is_global=False,
        required_args=(),
        args_picker_command_d=mosaic.put(d),
        commit_command_d=mosaic.put(d),
        commit_fn=mosaic.put(fn),
        )


def test_untyped_model_command_enum(system, args_picker_enum):
    enum = args_picker_enum(htypes.command.model_args_picker_command_enumerator)
    key, piece = command_cfg_item.resolve_untyped_command_cfg_item(enum)
    assert key is None
    assert piece == enum
    command = command_cfg_item.resolve_untyped_command_cfg_value(enum, key, system, '<unused-service-name>')
    assert isinstance(command, UnboundArgsPickerCommandEnumerator)


def test_untyped_ui_command_enum(system, args_picker_enum):
    enum = args_picker_enum(htypes.command.ui_args_picker_command_enumerator)
    key, piece = command_cfg_item.resolve_untyped_command_cfg_item(enum)
    assert key is None
    assert piece == enum
    command = command_cfg_item.resolve_untyped_command_cfg_value(enum, key, system, '<unused-service-name>')
    assert isinstance(command, UnboundArgsPickerCommandEnumerator)
