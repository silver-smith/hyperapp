from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.model_command import UnboundModelCommand
from .code.list_adapter import list_model_state_t
from .tested.code import details


def test_format_factory_k():
    command_d = htypes.details_tests.sample_command_d()
    k = htypes.details.factory_k(
        command_d=mosaic.put(command_d),
        )
    title = details.format_factory_k(k)
    assert type(title) is str



def _sample_fn():
    return 'sample-fn'


@mark.config_fixture('model_command_reg')
def model_command_reg_config(partial_ref):
    fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_fn,
        bound_fn=_sample_fn,
        )
    command = UnboundModelCommand(
        d=htypes.details_tests.sample_command_d(),
        ctx_fn=fn,
        properties=htypes.command.properties(False, False, False),
        )
    return {
        htypes.details_tests.sample_model: [command],
        }


@mark.fixture
def ctx():
    return Context()


@mark.fixture.obj
def model_t():
    return htypes.details_tests.sample_model


@mark.fixture.obj
def model(model_t):
    return model_t()


@mark.fixture
def model_state():
    model_state_t = list_model_state_t(htypes.details_tests.item)
    return model_state_t(
        current_idx=0,
        current_item=htypes.details_tests.item(id=1),
        )


def test_details_commands_service(details_commands, ctx, model_t):
    d_to_command = details_commands(model_t, ctx)
    assert type(d_to_command) is dict
    assert list(d_to_command) == [htypes.details_tests.sample_command_d()]


def test_command_list(details_commands, ctx, model, model_state):
    k_list = details.details_command_list(model, model_state, ctx, details_commands)
    assert type(k_list) is list
    assert len(k_list) == 1
