from unittest.mock import Mock, AsyncMock

from . import htypes
from .code.mark import mark


@mark.config_fixture('default_model_factory')
def default_model_factory_config():
    return {
        htypes.builtin.string: htypes.visualizer_fixtures.string_view_k(),
        htypes.builtin.int: htypes.visualizer_fixtures.int_view_k(),
        }


@mark.config_fixture('view_factory_reg')
def view_factory_reg_config():
    factory = AsyncMock()
    factory.call.return_value = htypes.visualizer_fixtures.sample_view()
    return {
        htypes.visualizer_fixtures.string_view_k(): factory,
        htypes.visualizer_fixtures.int_view_k(): factory,
        }


@mark.fixture
def view_fn_mock(piece):
    view_fn = Mock()
    view_fn.call.return_value.piece = piece
    return {piece._t: view_fn}


@mark.fixture
def visualizer_view_reg_config(view_fn_mock):
    return {
        **view_fn_mock(htypes.visualizer_fixtures.sample_view())
        }


@mark.config_fixture('view_reg')
def view_reg_config(visualizer_view_reg_config):
    return visualizer_view_reg_config
