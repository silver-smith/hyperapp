from hyperapp.common.htypes import tString, TList
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
        t = deduce_complex_value_type(mosaic, types, value)
        if t is tString:
            adapter_layout = htypes.str_adapter.static_str_adapter(value)
            return htypes.text.edit_layout(mosaic.put(adapter_layout))
        if isinstance(t, TList):
            adapter_layout = htypes.list_adapter.static_list_adapter(mosaic.put(value, t))
            return htypes.list.layout(mosaic.put(adapter_layout))
        if t is htypes.sample_list.sample_list:
            adapter_layout = htypes.list_adapter.fn_list_adapter(mosaic.put(value))
            return htypes.list.layout(mosaic.put(adapter_layout))
        raise NotImplementedError(type(value))
    return fn
