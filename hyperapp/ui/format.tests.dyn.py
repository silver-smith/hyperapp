from . import htypes
from .code.mark import mark
from .tested.code import format as format_module


def test_default_format(format):
    result = format(123)
    assert result == '123'


def format_sample_record(piece):
    return f'sample-record:{piece.value}'


@mark.config_fixture('formatter_creg')
def formatter_creg_config():
    return {
        htypes.format_tests.sample_record: format_sample_record,
        }


def test_formatter(format):
    piece = htypes.format_tests.sample_record(value=123)
    result = format(piece)
    assert result == 'sample-record:123'
