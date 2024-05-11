from . import htypes
from .services import (
    mark,
    )


@mark.model
def sample_record(piece):
    return htypes.sample_record.item(123, "Sample title")
