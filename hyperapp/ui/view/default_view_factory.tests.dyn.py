from unittest.mock import AsyncMock

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import default_view_factory


@mark.fixture
def sample_k_factory():
    return AsyncMock()


@mark.fixture
def view_factory_reg(sample_k_factory):
    return {
        htypes.default_view_factory_tests.sample_k(): sample_k_factory,
        }


@mark.config_fixture('default_model_factory')
def default_model_factory_config():
    return {
        htypes.default_view_factory_tests.sample_model: htypes.default_view_factory_tests.sample_k()
        }


def test_default_model_factory(default_model_factory, sample_k_factory):
    model_t = htypes.default_view_factory_tests.sample_model
    factory = default_model_factory(model_t)
    assert factory is sample_k_factory


@mark.config_fixture('default_ui_factory')
def default_ui_factory_config():
    return {
        htypes.model.index_list_ui_t: htypes.default_view_factory_tests.sample_k()
        }


def test_default_ui_factory(default_ui_factory, sample_k_factory):
    ui_t = htypes.model.index_list_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.default_view_factory_tests.sample_item),
        )
    factory = default_ui_factory(ui_t)
    assert factory is sample_k_factory
