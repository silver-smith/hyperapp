from unittest.mock import Mock, AsyncMock

from hyperapp.boot.htypes import tString, tInt

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import visualizer_fixtures
from .tested.code import visualizer as visualizer_module


@mark.fixture
def ctx():
    return Context()


async def test_string(visualizer, sample_string_view, ctx):
    view = await visualizer(ctx, htypes.builtin.string, accessor=None, inline=True)
    assert view == sample_string_view


async def test_int(visualizer, sample_int_view, ctx):
    view = await visualizer(ctx, htypes.builtin.int, accessor=None, properties={'inline': False})
    assert view == sample_int_view


async def test_static_list(visualizer, ctx):
    value = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        )
    view = await visualizer(ctx, deduce_t(value), accessor=None, properties=None)
    assert view == htypes.visualizer_tests.sample_view()


def sample_fn():
    pass


@mark.config_fixture('model_reg')
def model_reg_config():
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_fn),
        ctx_params=(),
        service_params=(),
        )
    return {
        htypes.visualizer_tests.sample_list: htypes.model.model(
            ui_t=mosaic.put(
                htypes.model.index_list_ui_t(
                    item_t=pyobj_creg.actor_to_ref(htypes.visualizer_tests.sample_list_item),
                    ),
                ),
            system_fn=mosaic.put(system_fn),
            ),
        }


@mark.config_fixture('default_ui_factory')
def default_ui_factory_config():
    return {
        htypes.model.index_list_ui_t: htypes.visualizer_tests.sample_k(),
        htypes.model.static_list_ui_t: htypes.visualizer_tests.sample_k(),
        }


@mark.config_fixture('view_factory_reg')
def view_factory_reg_config():
    k = htypes.visualizer_tests.sample_k()
    factory = AsyncMock()
    factory.call_ui_t.return_value = htypes.visualizer_tests.sample_view()
    return {k: factory}


async def test_sample_list(visualizer, ctx):
    model_t = htypes.visualizer_tests.sample_list
    view = await visualizer(ctx, model_t, accessor=None, properties=None)
    assert view == htypes.visualizer_tests.sample_view()


@mark.fixture
def model_layout_k():
    return htypes.ui.model_layout_k(
        model_t=pyobj_creg.actor_to_ref(htypes.builtin.string),
        )


def test_model_layout_k_resource_name(model_layout_k):
    gen = Mock()
    name = visualizer_module.model_layout_k_resource_name(model_layout_k, gen)
    assert type(name) is str


def test_format_model_layout_k(model_layout_k):
    title = visualizer_module.format_model_layout_k(model_layout_k)
    assert type(title) is str
