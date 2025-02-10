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
    d = htypes.wrap_view_tests.sample_d()
    factory = Mock()
    return {d: factory}


def test_wrap_view():
    ctx = Context()
    d = htypes.wrap_view_tests.sample_d()
    view_factory = htypes.view_factory.factory(
        d=mosaic.put(d),
        )
    view = Mock(piece=None)
    wrapper = wrap_view.wrap_view(view_factory, view, ctx)
