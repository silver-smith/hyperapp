from . import htypes
from .code.context import Context
from .tested.code import show_current_context


def test_current_context_list():
    ctx = Context(sample_context=12345)
    piece = htypes.show_current_context.view()
    result = show_current_context.current_context_list(piece, ctx)
    assert result
    assert result[0].name == 'sample_context'


def test_show_current_context():
    piece_1 = htypes.show_current_context_tests.sample_model_1()
    result_1 = show_current_context.show_current_context(piece_1)
    result_1 == htypes.show_current_context.view()
    piece_2 = htypes.show_current_context_tests.sample_model_2()
    result_2 = show_current_context.show_current_context(piece_2)
    result_2 == htypes.show_current_context.view()
