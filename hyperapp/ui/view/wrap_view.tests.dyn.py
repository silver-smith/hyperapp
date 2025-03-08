from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import wrap_view


@mark.config_fixture('view_factory_reg')
def view_factory_reg_config():
    k = htypes.wrap_view_tests.sample_k()
    factory = Mock()
    return {k: factory}


@mark.fixture
def view_reg():
    return Mock()


def test_wrap_view():
    ctx = Context()
    k = htypes.wrap_view_tests.sample_k()
    view_factory = htypes.view_factory.factory(
        model=None,
        k=mosaic.put(k),
        )
    hook = Mock()
    view = Mock(piece=None)
    wrapper = wrap_view.wrap_view(view_factory, view, hook, ctx)
    hook.replace_view.assert_called_once()
