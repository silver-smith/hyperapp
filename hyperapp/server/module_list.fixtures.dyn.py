from . import htypes
from .services import (
    mark,
    )


@mark.param.ModuleList
def piece():
    return htypes.module_list.module_list(status=None)


@mark.param.ModuleList.open
def current_key():
    return 'common.bundler'
