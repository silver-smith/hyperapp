from . import htypes
from .services import (
    mark,
    mosaic,
    )


@mark.service
def visualizer():
    def fn(value):
        if type(value) is not str:
            raise NotImplementedError(type(value))
        adapter_layout = htypes.str_adapter.static_str_adapter(value)
        return htypes.text.edit_layout(mosaic.put(adapter_layout))
    return fn
