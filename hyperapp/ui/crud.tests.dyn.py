from . import htypes
from .code.context import Context
from .tested.code import crud


def test_open():
    piece = htypes.crud.crud_open_command_fn(
        name='edit',
        key_field='id',
        init_action='get',
        commit_action='update',
        )
    ctx = Context(
        model=htypes.crud_tests.sample_model(),
        current_item=htypes.crud_tests.sample_item(id=123),
        )
    fn = crud.CrudOpenFn.from_piece(piece)
    assert not fn.missing_params(ctx)
    assert fn.missing_params(Context()) == {'model', 'current_item'}
    form = fn.call(ctx)
    assert isinstance(form, htypes.crud.form)
