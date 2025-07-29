from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .tested.code import builtins_format


def _sample_fn():
    pass


@mark.fixture
def module():
    attr = pyobj_creg.actor_to_piece(_sample_fn)
    return web.summon(attr.object)


def test_attribute(module):
    piece = htypes.builtin.attribute(
        object=mosaic.put(module),
        attr_name='sample-attr',
        )
    title = builtins_format.format_attribute(piece)
    assert type(title) is str


def test_python_module(module):
    title = builtins_format.format_python_module(module)
    assert type(title) is str
