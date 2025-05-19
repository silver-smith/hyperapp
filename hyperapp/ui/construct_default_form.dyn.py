from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.type_convertor import type_to_text_convertor


async def construct_default_form(visualizer, ctx, record_adapter, record_t):
    element_list = []
    for name, t in record_t.fields.items():
        label_view = htypes.label.view(name)
        label_element = htypes.box_layout.element(
            view=mosaic.put(label_view),
            focusable=False,
            stretch=0,
            )
        field_accessor = htypes.accessor.record_field_accessor(
            record_adapter=mosaic.put(record_adapter),
            field_name=name,
            )
        field_view = await visualizer(ctx, t, accessor=field_accessor)
        element = htypes.box_layout.element(
            view=mosaic.put(field_view),
            focusable=True,
            stretch=0,
            )
        element_list += [label_element, element]
    stretch = htypes.box_layout.element(
        view=None,
        focusable=False,
        stretch=1,
        )
    element_list.append(stretch)
    return htypes.form.view(
        direction='TopToBottom',
        elements=tuple(element_list),
        adapter=mosaic.put(record_adapter),
        )
