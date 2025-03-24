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


def test_command_list(global_model_command_reg, get_model_commands):
    ctx = Context()
    model_state_t = list_model_state_t(htypes.details_tests.item)
    model_state = model_state_t(
        current_idx=0,
        current_item=htypes.details_tests.item(id=1),
        )
    model = htypes.details_tests.sample_model()
    k_list = details.details_command_list(model, model_state, ctx, global_model_command_reg, get_model_commands)
    assert type(k_list) is list
    assert len(k_list) == 1
