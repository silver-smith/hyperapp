import weakref

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import system_fn


class PhonyWidget:
    pass


class PhonyView:

    def widget_state(self, widget):
        return 'a-state'


def _sample_fn(view, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture.obj
def sample_service():
    return 'a-service'


@mark.fixture
def view():
    return PhonyView()


# Should hold ref to it.
@mark.fixture
def widget():
    return PhonyWidget()


@mark.fixture.obj
def piece():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('view', 'state'),
        service_params=('sample_service',),
        )


def test_construct(system_fn_creg, piece):
    fn = system_fn_creg.animate(piece)
    assert isinstance(fn, system_fn.ContextFn)
    assert fn.piece == piece


def test_call(system_fn_creg, view, widget, piece):
    ctx = Context(
        view=view,
        widget=weakref.ref(widget),
        )
    fn = system_fn_creg.animate(piece)
    result = fn.call(ctx)
    assert result == 'sample-fn: a-state, a-service', repr(result)
