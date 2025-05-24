from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.type_convertor import type_to_text_convertor


@mark.actor.formatter_creg
def format_factory_k(piece, format):
    base_factory_k = web.summon(piece.base_factory_k)
    base = format(base_factory_k)
    return f"{piece.field_name}: {base}"


def record_field_list(model, ctx, view_factory_reg):
    record_t = pyobj_creg.invite(model.record_t)
    k_list = []
    for name, t in record_t.fields.items():
        for item in view_factory_reg.items(ctx, model_t=t, only_model=True):
            k = htypes.crud_field_view_factory.factory_k(
                field_name=name,
                field_t=pyobj_creg.actor_to_ref(t),
                base_factory_k=item.k
                )
            k_list.append(k)
    return k_list


async def record_field_get(k, ctx, view_factory_reg):
    base_factory_k = web.summon(k.base_factory_k)
    base_factory = view_factory_reg[base_factory_k]
    record_adapter = htypes.crud.record_adapter()
    field_t = pyobj_creg.invite(k.field_t)
    accessor = htypes.accessor.record_field_accessor(
        record_adapter=mosaic.put(record_adapter),
        field_name=k.field_name,
        )
    return await base_factory.call(ctx, model_t=field_t, accessor=accessor)
