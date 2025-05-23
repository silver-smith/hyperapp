from unittest.mock import Mock, AsyncMock

from . import htypes
from .code.mark import mark


@mark.config_fixture('default_model_factory')
def default_model_factory_config():
    return {
        htypes.builtin.string: htypes.visualizer_fixtures.string_view_k(),
        htypes.builtin.int: htypes.visualizer_fixtures.int_view_k(),
        }


@mark.fixture.obj
def sample_string_view():
    return htypes.visualizer_fixtures.sample_string_view()


@mark.fixture.obj
def sample_int_view():
    return htypes.visualizer_fixtures.sample_int_view()


@mark.config_fixture('view_factory_reg')
def view_factory_reg_config(sample_string_view, sample_int_view):
    string_view_factory = AsyncMock()
    string_view_factory.call.return_value = sample_string_view
    int_view_factory = AsyncMock()
    int_view_factory.call.return_value = sample_int_view
    return {
        htypes.visualizer_fixtures.string_view_k(): string_view_factory,
        htypes.visualizer_fixtures.int_view_k(): int_view_factory,
        }


@mark.fixture
def view_fn_mock(piece):
    view_fn = Mock()
    view_fn.call.return_value.piece = piece
    return {piece._t: view_fn}


@mark.fixture
def visualizer_view_reg_config(view_fn_mock):
    return {
        **view_fn_mock(htypes.visualizer_fixtures.sample_string_view()),
        **view_fn_mock(htypes.visualizer_fixtures.sample_int_view()),
        }


@mark.config_fixture('view_reg')
def view_reg_config(visualizer_view_reg_config):
    return visualizer_view_reg_config
