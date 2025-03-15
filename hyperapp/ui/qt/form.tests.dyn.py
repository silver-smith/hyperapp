from unittest.mock import Mock

from hyperapp.boot.htypes import tInt

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.construct_default_form import construct_default_form
from .fixtures import qapp_fixtures, feed_fixtures
from .tested.code import form


def _sample_form_fn(piece):
    assert isinstance(piece, htypes.form_tests.sample_form), repr(piece)
    return htypes.form_tests.value(123, "Sample  text")


@mark.fixture
def model():
    return htypes.form_tests.sample_form()


@mark.fixture
def ctx(model):
    return Context(
        model=model,
        )


@mark.fixture
def adapter_piece():
    item_t_res = pyobj_creg.actor_to_piece(htypes.form_tests.value)
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_form_fn),
        ctx_params=('piece',),
        service_params=(),
        )
    return htypes.record_adapter.fn_record_adapter(
        record_t=mosaic.put(item_t_res),
        system_fn=mosaic.put(system_fn),
        )


@mark.fixture
def piece(adapter_piece):
    return construct_default_form(adapter_piece, htypes.form_tests.value)


@mark.fixture
def state():
    return None


@mark.config_fixture('model_layout_reg')
def model_layout_reg_config():
    def k(t):
        return htypes.ui.model_layout_k(pyobj_creg.actor_to_ref(t))
    return {
        k(htypes.builtin.int): htypes.text.edit_view(
            adapter=mosaic.put(htypes.int_adapter.int_adapter()),
            ),
        k(htypes.builtin.string): htypes.text.edit_view(
            adapter=mosaic.put(htypes.str_adapter.static_str_adapter()),
            ),
        }


def test_form(qapp, model, ctx, piece):
    state = None
    view = form.FormView.from_piece(piece, model, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece == piece
    state = view.widget_state(widget)
    assert state


@mark.config_fixture('view_factory_reg')
def view_factory_reg_config():
    k = htypes.form_tests.sample_k()
    factory = Mock()
    factory.call.return_value = htypes.label.view("Sample label")
    return {k: factory}


@mark.fixture
def view_factory():
    k = htypes.form_tests.sample_k()
    return htypes.view_factory.factory(
        model=None,
        k=mosaic.put(k),
        )


@mark.fixture
def ctl_hook():
    return Mock()


@mark.fixture
def view(view_reg, piece, ctx, ctl_hook):
    view = view_reg.animate(piece, ctx)
    view.set_controller_hook(ctl_hook)
    return view


@mark.fixture
def widget(view, state, ctx):
    return  view.construct_widget(state, ctx)
