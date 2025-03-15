from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )


def construct_default_form(record_adapter, record_t):
    element_list = []
    for name, t in record_t.fields.items():
        label_view = htypes.label.view(name)
        label_element = htypes.box_layout.element(
            view=mosaic.put(label_view),
            focusable=False,
            stretch=0,
            )
        field_adapter = htypes.record_field_adapter.record_field_adapter(
            record_adapter=mosaic.put(record_adapter),
            field_name=name,
            field_t=pyobj_creg.actor_to_ref(t),
            )
        # TODO: Investigate how to amend and use visualizer.
        field_view = htypes.line_edit.edit_view(
            adapter=mosaic.put(field_adapter),
            )
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
