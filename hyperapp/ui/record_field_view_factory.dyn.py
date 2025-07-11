from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark


@mark.actor.formatter_creg
def format_factory_k(piece, format):
    base_factory_k = web.summon(piece.base_factory_k)
    base = format(base_factory_k)
    return f"{piece.field_name}: {base}"


def record_field_list(ui_t, system_fn, ctx, view_factory_reg):
    record_t = pyobj_creg.invite(ui_t.record_t)
    k_list = []
    for name, t in record_t.fields.items():
        for item in view_factory_reg.items(ctx, model_t=t, only_model=True):
            k = htypes.record_field_view_factory.factory_k(
                field_name=name,
                field_t=pyobj_creg.actor_to_ref(t),
                record_t=ui_t.record_t,
                system_fn=mosaic.put(system_fn.piece),
                base_factory_k=item.k
                )
            k_list.append(k)
    return k_list


async def record_field_get(k, ctx, view_factory_reg):
    base_factory_k = web.summon(k.base_factory_k)
    base_factory = view_factory_reg[base_factory_k]
    record_adapter = htypes.record_adapter.fn_record_adapter(
        record_t=k.record_t,
        system_fn=k.system_fn,
        )
    field_t = pyobj_creg.invite(k.field_t)
    accessor = htypes.accessor.record_field_accessor(
        record_adapter=mosaic.put(record_adapter),
        field_name=k.field_name,
        )
    return await base_factory.call(ctx, model_t=field_t, accessor=accessor)
