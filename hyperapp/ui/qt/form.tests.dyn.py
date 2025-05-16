from unittest.mock import Mock

from hyperapp.boot.htypes import tInt

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .fixtures import qapp_fixtures
from .fixtures import feed_fixtures
from .fixtures import visualizer_fixtures
from .tested.code import form


def _sample_record_model(piece):
    assert isinstance(piece, htypes.form_tests.sample_form), repr(piece)
    return htypes.form_tests.value(123, "Sample  text")


@mark.fixture
def sample_record_model_fn(rpc_system_call_factory):
    return ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('piece',),
        service_params=(),
        raw_fn=_sample_record_model,
        )


@mark.fixture.obj
def model():
    return htypes.form_tests.sample_form()


@mark.fixture
def ctx(model):
    return Context(
        model=model,
        )


@mark.fixture
def adapter_piece(sample_record_model_fn):
    item_t_res = pyobj_creg.actor_to_piece(htypes.form_tests.value)
    return htypes.record_adapter.fn_record_adapter(
        record_t=mosaic.put(item_t_res),
        system_fn=mosaic.put(sample_record_model_fn.piece),
        )


@mark.fixture
async def piece(visualizer, ctx, adapter_piece):
    label = htypes.label.view("Sample label")
    field_adapter = htypes.record_field_adapter.record_field_adapter(
        record_adapter=mosaic.put(adapter_piece),
        field_name='text',
        field_t=pyobj_creg.actor_to_ref(htypes.builtin.string),
        )
    field_view = htypes.line_edit.readonly_view(
        adapter=mosaic.put(field_adapter),
        )
    element_list = [
        htypes.box_layout.element(
            view=mosaic.put(label),
            focusable=False,
            stretch=0,
            ),
        htypes.box_layout.element(
            view=mosaic.put(field_view),
            focusable=True,
            stretch=0,
            ),
        htypes.box_layout.element(
            view=None,
            focusable=False,
            stretch=1,
            ),
        ]
    return htypes.form.view(
        direction='TopToBottom',
        elements=tuple(element_list),
        adapter=mosaic.put(adapter_piece),
        )



@mark.fixture
def state():
    return None


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


async def test_form_view_factory(ctx, sample_record_model_fn):
    piece = htypes.model.record_ui_t(
        record_t=pyobj_creg.actor_to_ref(htypes.record_adapter_tests.item),
        )
    view = await form.form_view_factory(piece, sample_record_model_fn, ctx)
    assert isinstance(view, htypes.form.view)
