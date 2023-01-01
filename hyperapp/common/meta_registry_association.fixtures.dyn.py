from hyperapp.common.code_registry import CodeRegistry

from .code import mark
from .services import (
    types,
    web,
    )


@mark.param.register_meta
def piece():
    return None


@mark.service
def meta_registry():
    return CodeRegistry('phony-meta', web, types)
