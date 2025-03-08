from . import htypes
from .tested.code import record_field_view_factory


def test_list():
    piece = htypes.record_field_view_factory_tests.sample_model(
        str_field="Sample str",
        )
    k_list = record_field_view_factory.record_field_list(piece)
    assert k_list
