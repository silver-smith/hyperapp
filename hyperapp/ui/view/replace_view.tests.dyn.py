from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import replace_view


@mark.config_fixture('view_factory_reg')
def view_factory_reg_config():
    d = htypes.replace_view_tests.sample_d()
    factory = Mock()
    return {d: factory}


@mark.fixture
def view_reg():
    return Mock()


def test_replace_view():
    ctx = Context()
    d = htypes.replace_view_tests.sample_d()
    view_factory = htypes.view_factory.factory(
        d=mosaic.put(d),
        )
    hook = Mock()
    view = Mock(piece=None)
    replaceper = replace_view.replace_view(view_factory, view, hook, ctx)
    hook.replace_view.assert_called_once()
