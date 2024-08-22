from . import htypes
from .code.mark import mark


@mark.model
def sample_record(piece):
    return htypes.sample_record.item(123, "Sample title")


def open_sample_fn_record():
    return htypes.sample_record.sample_record()
