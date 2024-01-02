from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    mark,
    mosaic,
    types,
    )


@mark.service
def visualizer():
    def fn(value):
        if type(value) is str:
            adapter_layout = htypes.str_adapter.static_str_adapter(value)
            return htypes.text.edit_layout(mosaic.put(adapter_layout))
        if type(value) is list:
            t = deduce_complex_value_type(mosaic, types, value)
            adapter_layout = htypes.list_adapter.static_list_adapter(mosaic.put(value, t))
            return htypes.list.layout(mosaic.put(adapter_layout))
        raise NotImplementedError(type(value))
    return fn
