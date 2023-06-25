from . import htypes
from .services import (
    mark,
    )


@mark.global_command
def open_sample_list():
    return htypes.sample_list.sample_list(provider='client')
