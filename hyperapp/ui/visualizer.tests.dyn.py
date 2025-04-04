from unittest.mock import Mock

from hyperapp.boot.htypes import tString, tInt

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.fn_list_adapter import index_list_ui_type_layout
from .tested.code import visualizer as visualizer_module


@mark.fixture
def ctx():
    return Context()


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


def test_string(visualizer, ctx):
    layout = visualizer(ctx, "")
    assert isinstance(layout, htypes.text.edit_view)


def test_int(visualizer, ctx):
    layout = visualizer(ctx, 1)
    assert isinstance(layout, htypes.text.edit_view)


def test_list(visualizer, ctx):
    value = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        )
    layout = visualizer(ctx, value)
    assert isinstance(layout, htypes.list.view)


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
                htypes.model.list_ui_t(
                    item_t=pyobj_creg.actor_to_ref(htypes.visualizer_tests.sample_list_item),
                    ),
                ),
            system_fn=mosaic.put(system_fn),
            ),
        }


@mark.config_fixture('ui_type_creg')
def ui_type_creg_config():
    return {
        htypes.model.list_ui_t: index_list_ui_type_layout,
        }


def test_sample_list(visualizer, ctx):
    model = htypes.visualizer_tests.sample_list()
    layout = visualizer(ctx, model)
    assert isinstance(layout, htypes.list.view)


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
