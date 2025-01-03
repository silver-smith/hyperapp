from unittest.mock import Mock

from hyperapp.common.htypes import tString, tInt

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.fn_list_adapter import list_ui_type_layout
from .tested.code import visualizer as visualizer_module


@mark.fixture
def lcs():
    lcs = Mock()
    # Fall thru to default layout.
    lcs.get.return_value = None
    return lcs


@mark.fixture
def ctx():
    return Context()


@mark.config_fixture('model_layout_creg')
def model_layout_creg_config():
    return {
        tString: visualizer_module.string_layout,
        tInt: visualizer_module.int_layout,
        }


def test_model_layout_creg(model_layout_creg, lcs, ctx):
    layout = model_layout_creg.animate("Some string", lcs, ctx)
    assert isinstance(layout, htypes.text.edit_view)


def test_string_layout(lcs, ctx):
    layout = visualizer_module.string_layout("<unused>", lcs, ctx)
    assert isinstance(layout, htypes.text.edit_view)


def test_int_layout(lcs, ctx):
    layout = visualizer_module.int_layout(12345, lcs, ctx)
    assert isinstance(layout, htypes.text.edit_view)


def test_string(visualizer, lcs, ctx):
    layout = visualizer(lcs, ctx, "Sample text")
    assert layout


def test_int(visualizer, lcs, ctx):
    layout = visualizer(lcs, ctx, 12345)
    assert layout


def test_list(visualizer, lcs, ctx):
    value = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        )
    layout = visualizer(lcs, ctx, value)
    assert layout


def sample_fn():
    pass


@mark.config_fixture('visualizer_reg')
def visualizer_config():
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
        htypes.model.list_ui_t: list_ui_type_layout,
        }


def test_sample_list(visualizer, lcs, ctx):
    piece = htypes.visualizer_tests.sample_list()
    layout = visualizer(lcs, ctx, piece)
    assert isinstance(layout, htypes.list.view)


def test_set_custom_layout(set_custom_layout, lcs):
    piece = htypes.visualizer_tests.sample_piece
    layout = htypes.visualizer_tests.sample_layout()
    set_custom_layout(lcs, piece, layout)
    lcs.set.assert_called_once()
