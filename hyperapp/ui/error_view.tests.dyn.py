from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import error_view


@mark.config_fixture('model_layout_reg')
def model_layout_reg_config():
    def k(t):
        return htypes.ui.model_layout_k(pyobj_creg.actor_to_ref(t))
    return {
        k(htypes.builtin.string): htypes.text.edit_view(
            adapter=mosaic.put(htypes.str_adapter.static_str_adapter()),
            ),
        }


def test_error_view(error_view):
    ctx = Context()
    exception = RuntimeError("Shit happens")
    model, view = error_view(exception, ctx)
    assert model
    assert view
