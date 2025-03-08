from . import htypes
from .services import (
    deduce_t,
    )


def record_field_list(piece):
    model_t = deduce_t(piece)
    k_list = []
    for name in model_t.fields:
        k = htypes.record_field_view_factory.factory_k(
            field_name=name,
            )
        k_list.append(k)
    return k_list


def record_field_get(k):
    adapter = htypes.record_field_adapter.record_field_adapter(
        record_adapter=None,
        field_name=k.field_name,
        )
