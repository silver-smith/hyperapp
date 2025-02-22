import logging
import weakref
from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.selector import Selector
from .fixtures import qapp_fixtures
from .tested.code import crud

log = logging.getLogger(__name__)


def _sample_crud_get(piece, id):
    assert isinstance(piece, htypes.crud_tests.sample_model), piece
    if id == 11:
        return htypes.crud_tests.sample_record(id, f'item#{id}')
    if id == 22:
        return htypes.crud_tests.sample_selector()
    assert id == 33
    return "Default string value"


def _sample_crud_update(piece, id, value):
    assert isinstance(piece, htypes.crud_tests.sample_model), piece
    if id == 11:
        assert isinstance(value, htypes.crud_tests.sample_record), value
    elif id == 22:
        assert isinstance(value, htypes.crud_tests.sample_selector), value
    elif id == 33:
        assert type(value) is str, value
    else:
        assert 0, id
    log.info("Update %s: #%d -> %s", piece, id, value)


@mark.fixture
def _sample_crud_get_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_crud_get),
        ctx_params=('piece', 'id'),
        service_params=(),
        )


@mark.fixture
def _sample_crud_update_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_crud_update),
        ctx_params=('piece', 'id', 'value'),
        service_params=(),
        )


def _sample_selector_get(value):
    assert isinstance(value, htypes.crud_tests.sample_selector), value
    return htypes.crud_tests.sample_selector_model()


def _sample_selector_pick(piece, current_item):
    assert isinstance(piece, htypes.crud_tests.sample_selector_model), piece
    assert isinstance(current_item, htypes.crud_tests.sample_selector_item)
    return htypes.crud_tests.sample_selector()


@mark.fixture
def _sample_selector_get_fn(partial_ref):
    return ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('value',),
        service_params=(),
        raw_fn=_sample_selector_get,
        bound_fn=_sample_selector_get,
        )


@mark.fixture
def _sample_selector_pick_fn(partial_ref):
    return ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('piece', 'current_item'),
        service_params=(),
        raw_fn=_sample_selector_pick,
        bound_fn=_sample_selector_pick,
        )


@mark.fixture
def lcs():
    lcs = Mock()
    lcs.get.return_value = None  # Used by visualizer.
    return lcs


@mark.fixture
def navigator_widget():
    return Mock()


@mark.fixture
def navigator_rec(navigator_widget):
    return Mock(view=Mock(), widget_wr=weakref.ref(navigator_widget))


@mark.fixture
def ctx(lcs, navigator_rec):
    return Context(
        lcs=lcs,
        navigator=navigator_rec,
        )


@mark.fixture
def model():
    return htypes.crud_tests.sample_model()


@mark.fixture
def view_piece_ctr(_sample_crud_get_fn, _sample_crud_update_fn, model, item_id, pick_fn):
    base_view_piece = htypes.label.view("Sample label")
    return htypes.crud.view(
        base_view=mosaic.put(base_view_piece),
        label="Sample CRUD context",
        model=mosaic.put(model),
        commit_command_d=mosaic.put(htypes.crud_tests.save_d()),
        args=(htypes.crud.arg('id', mosaic.put(item_id)),),
        pick_fn=mosaic.put_opt(pick_fn),
        commit_fn=mosaic.put(_sample_crud_update_fn),
        commit_value_field='value',
        )


def test_context_view(qapp, ctx, view_piece_ctr):
    piece = view_piece_ctr(11, pick_fn=None)
    view = crud.CrudContextView.from_piece(piece, ctx)
    state = None
    widget = view.construct_widget(state, ctx)
    assert view.piece == piece
    state = view.widget_state(widget)
    assert state


@mark.fixture
def run_open_command_fn_test(ctx, navigator_rec, _sample_crud_get_fn, _sample_crud_update_fn, value_t, item_id):
    piece = htypes.crud.open_command_fn(
        name='edit',
        value_t=pyobj_creg.actor_to_ref(value_t),
        key_fields=('id',),
        init_action_fn=mosaic.put(_sample_crud_get_fn),
        commit_command_d=mosaic.put(htypes.crud_tests.save_d()),
        commit_action_fn=mosaic.put(_sample_crud_update_fn),
        )
    fn = crud.CrudOpenFn.from_piece(piece)

    assert fn.missing_params(Context()) == {'navigator', 'model', 'current_item'}
    ctx = ctx.clone_with(
        navigator=navigator_rec,
        model=htypes.crud_tests.sample_model(),
        current_item=htypes.crud_tests.sample_item(id=item_id),
        )
    assert not fn.missing_params(ctx)
    new_model = fn.call(ctx)
    navigator_rec.view.open.assert_called_once()


def test_open_command_fn_to_form(run_open_command_fn_test):
    value_t = htypes.crud_tests.sample_record
    run_open_command_fn_test(value_t, item_id=11)


def test_open_command_fn_to_str(run_open_command_fn_test):
    value_t = htypes.builtin.string
    run_open_command_fn_test(value_t, item_id=33)


@mark.config_fixture('selector_reg')
def selector_reg_config(_sample_selector_get_fn, _sample_selector_pick_fn):
    value_t = htypes.crud_tests.sample_selector
    selector = Selector(
        get_fn=_sample_selector_get_fn,
        pick_fn=_sample_selector_pick_fn,
        )
    return {value_t: selector}


@mark.config_fixture('model_layout_creg')
def model_layout_config():
    return {
        htypes.crud_tests.sample_selector_model:
            lambda piece, lcs, ctx: htypes.crud_tests.selector_view(),
        }


@mark.config_fixture('view_reg')
def view_reg_config():
    return {
        htypes.crud_tests.selector_view: Mock(),
        }


def test_open_command_fn_to_selector(run_open_command_fn_test):
    value_t = htypes.crud_tests.sample_selector
    run_open_command_fn_test(value_t, item_id=22)


async def test_command_enum_for_form(view_reg, lcs, ctx, view_piece_ctr, model):
    view_piece = view_piece_ctr(11, pick_fn=None)
    view = view_reg.animate(view_piece, ctx)
    commands = crud.crud_commit_command_enum(view, lcs)
    assert commands
    [unbound_cmd] = commands
    assert unbound_cmd.properties
    value = htypes.crud_tests.sample_record(12345, "Some text")
    input = Mock()
    input.get_value.return_value = value
    command_ctx = ctx.clone_with(
        model=model,
        piece=model,
        input=input,
        )
    bound_cmd = unbound_cmd.bind(command_ctx)
    assert bound_cmd.enabled
    await bound_cmd.run()


async def test_command_enum_for_selector(view_reg, lcs, ctx, _sample_selector_pick_fn, view_piece_ctr):
    view_piece = view_piece_ctr(22, pick_fn=_sample_selector_pick_fn.piece)
    view = view_reg.animate(view_piece, ctx)
    commands = crud.crud_commit_command_enum(view, lcs)
    assert commands
    [unbound_cmd] = commands
    assert unbound_cmd.properties
    model = htypes.crud_tests.sample_selector_model()
    current_item = htypes.crud_tests.sample_selector_item()
    command_ctx = ctx.clone_with(
        model=model,
        piece=model,
        current_item=current_item,
        )
    bound_cmd = unbound_cmd.bind(command_ctx)
    assert bound_cmd.enabled
    await bound_cmd.run()
