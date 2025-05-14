from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.system_fn import ContextFn
from .tested.code import visualizer_reg as visualizer_reg_module


def _sample_fn():
    pass


@mark.config_fixture('model_reg')
def model_reg_config(rpc_system_call_factory):
    fn = ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_fn,
        )
    return {
        htypes.builtin.string: htypes.model.model(
            ui_t=mosaic.put("Unused ui_t"),
            system_fn=mosaic.put(fn.piece),
            ),
        }


def test_visualizer_reg(visualizer_reg):
    ui_t, system_fn = visualizer_reg(htypes.builtin.string)
    assert system_fn
