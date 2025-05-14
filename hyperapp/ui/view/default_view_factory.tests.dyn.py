from unittest.mock import AsyncMock

from . import htypes
from .code.mark import mark
from .tested.code import default_view_factory


@mark.config_fixture('default_model_t_factory')
def default_model_t_factory_config():
    return {
        htypes.default_view_factory_tests.sample_model: htypes.default_view_factory_tests.sample_k()
        }


@mark.fixture
def sample_k_factory():
    return AsyncMock()


@mark.fixture
def view_factory_reg(sample_k_factory):
    return {
        htypes.default_view_factory_tests.sample_k(): sample_k_factory,
        }


def test_default_model_t_factory(default_model_t_factory, sample_k_factory):
    model_t = htypes.default_view_factory_tests.sample_model
    factory = default_model_t_factory(model_t)
    assert factory is sample_k_factory
