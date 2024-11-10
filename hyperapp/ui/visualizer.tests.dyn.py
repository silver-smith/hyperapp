from unittest.mock import Mock

from hyperapp.common.htypes import tString, tInt

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import visualizer as visualizer_module


@mark.fixture
def lcs():
    lcs = Mock()
    # Fall thru to default layout.
    lcs.get.return_value = None
    return lcs


@mark.config_fixture('model_layout_creg')
def model_layout_creg_config():
    return {
        tString: visualizer_module.string_layout,
        tInt: visualizer_module.int_layout,
        }


def test_model_layout_creg(model_layout_creg):
    layout = model_layout_creg.animate("Some string")
    assert isinstance(layout, htypes.text.edit_view)


def test_string_layout():
    layout = visualizer_module.string_layout("<unused>")
    assert isinstance(layout, htypes.text.edit_view)


def test_int_layout():
    layout = visualizer_module.int_layout(12345)
    assert isinstance(layout, htypes.text.edit_view)


def test_string(visualizer, lcs):
    layout = visualizer(lcs, "Sample text")
    assert layout


def test_int(visualizer, lcs):
    layout = visualizer(lcs, 12345)
    assert layout


def test_list(visualizer, lcs):
    value = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        )
    layout = visualizer(lcs, value)
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
        htypes.visualizer_tests.sample_tree: htypes.model.model(
            ui_t=mosaic.put(
                htypes.model.tree_ui_t(
                    # key_t=pyobj_creg.actor_to_ref(htypes.visualizer_tests.sample_tree_key),
                    item_t=pyobj_creg.actor_to_ref(htypes.visualizer_tests.sample_tree_item),
                    ),
                ),
            system_fn=mosaic.put(system_fn),
            ),
        htypes.visualizer_tests.sample_record: htypes.model.model(
            ui_t=mosaic.put(
                htypes.model.record_ui_t(
                    record_t=pyobj_creg.actor_to_ref(htypes.visualizer_tests.sample_record_item),
                    ),
                ),
            system_fn=mosaic.put(system_fn),
            ),
        }


def test_sample_list(visualizer, lcs):
    piece = htypes.visualizer_tests.sample_list()
    layout = visualizer(lcs, piece)
    assert isinstance(layout, htypes.list.view)


def test_sample_tree(visualizer, lcs):
    piece = htypes.visualizer_tests.sample_tree()
    layout = visualizer(lcs, piece)
    assert isinstance(layout, htypes.tree.view)


def test_sample_record(visualizer, lcs):
    piece = htypes.visualizer_tests.sample_record()
    layout = visualizer(lcs, piece)
    assert isinstance(layout, htypes.form.view)


def test_set_custom_layout(set_custom_layout, lcs):
    piece = htypes.visualizer_tests.sample_piece
    layout = htypes.visualizer_tests.sample_layout()
    set_custom_layout(lcs, piece, layout)
    lcs.set.assert_called_once()
