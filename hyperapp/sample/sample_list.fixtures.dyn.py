from . import htypes
from .services import (
    mark,
    )


@mark.param.SampleList
def piece():
    return htypes.sample_list.sample_list(provider='fixture')


@mark.param.SampleList.open
def current_key():
    return 123
