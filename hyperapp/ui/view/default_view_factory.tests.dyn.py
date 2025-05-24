from unittest.mock import AsyncMock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import default_view_factory


@mark.fixture
def sample_1_k_factory():
    return AsyncMock()


@mark.fixture
def view_factory_reg(sample_1_k_factory):
    return {
        htypes.default_view_factory_tests.sample_1_k(): sample_1_k_factory,
        }


@mark.config_fixture('default_model_factory')
def default_model_factory_config():
    layout_1_k = htypes.default_view_factory_tests.sample_1_k()
    layout_2_k = htypes.default_view_factory_tests.sample_2_k()
    factory_1 = htypes.ui.default_model_factory(
        properties=(
            htypes.ui.property('inline', False),
            ),
        layout_k=mosaic.put(layout_1_k),
        )
    factory_2 = htypes.ui.default_model_factory(
        properties=(
            htypes.ui.property('inline', True),
            ),
        layout_k=mosaic.put(layout_1_k),
        )
    return {
        htypes.default_view_factory_tests.sample_model: [
            factory_1,
            factory_2,
            ],
        }


def test_default_model_factory(default_model_factory, sample_1_k_factory):
    model_t = htypes.default_view_factory_tests.sample_model
    properties = {'inline': False}
    factory = default_model_factory(model_t, properties)
    assert factory is sample_1_k_factory


@mark.config_fixture('default_ui_factory')
def default_ui_factory_config():
    return {
        htypes.model.index_list_ui_t: htypes.default_view_factory_tests.sample_1_k()
        }


def test_default_ui_factory(default_ui_factory, sample_1_k_factory):
    ui_t = htypes.model.index_list_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.default_view_factory_tests.sample_item),
        )
    factory = default_ui_factory(ui_t)
    assert factory is sample_1_k_factory
