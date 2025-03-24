from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
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


def details_command():
    return 'details-model'


@mark.fixture
def command_d():
    return htypes.details_tests.sample_command_d()


@mark.config_fixture('model_command_reg')
def model_command_reg_config(partial_ref, command_d):
    fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=(),
        raw_fn=details_command,
        bound_fn=details_command,
        )
    command = UnboundModelCommand(
        d=command_d,
        ctx_fn=fn,
        properties=htypes.command.properties(False, False, False),
        )
    return {
        htypes.details_tests.sample_model: [command],
        }


@mark.fixture
def details_view():
    return htypes.text.edit_view(
        adapter=mosaic.put(htypes.str_adapter.static_str_adapter()),
        )


@mark.config_fixture('model_layout_reg')
def model_layout_reg_config(details_view):
    def k(t):
        return htypes.ui.model_layout_k(pyobj_creg.actor_to_ref(t))
    return {
        k(htypes.builtin.string): details_view,
        }


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


@mark.fixture
def ctx(model, model_state):
    return Context(
        model=model,
        model_state=model_state,
        )


def test_view(ctx, command_d, model_state, details_view):
    piece = htypes.details.view(
        command_d=mosaic.put(command_d),
        model_state=mosaic.put(model_state),
        details_model=mosaic.put(details_command()),
        details_view=mosaic.put(details_view),
        )
    view = details.DetailsView.from_piece(piece, ctx)
    assert view.piece == piece
    assert view.children_context(ctx).model == details_command()


def test_details_commands_service(details_commands, ctx, command_d, model_t):
    d_to_command = details_commands(model_t, ctx)
    assert type(d_to_command) is dict
    assert list(d_to_command) == [command_d]


def test_command_list(details_commands, ctx, model, model_state):
    k_list = details.details_command_list(model, model_state, ctx, details_commands)
    assert type(k_list) is list
    assert len(k_list) == 1


async def test_get(visualizer, details_commands, ctx, command_d, model, model_state):
    k = htypes.details.factory_k(
        command_d=mosaic.put(command_d),
        )
    view_piece = await details.details_get(k, model, model_state, ctx, visualizer, details_commands)
