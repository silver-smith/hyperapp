import logging

from ..common.interface import form as form_types
from .module import Module
from .object import Object
from .view import View

log = logging.getLogger(__name__)


class FormObject(Object):

    impl_id = 'form'

    @classmethod
    def from_state(cls, field_object_map, state):
        return cls(field_object_map, state)

    def __init__(self, field_object_map, state):
        super().__init__()

    def get_title(self):
        return 'form'

    def get_state(self):
        return form_types.form_object(self.impl_id)


class FormView(View):

    impl_id = 'form'

    @classmethod
    async def from_state(cls, locale, state, parent, objimpl_registry, view_registry):
        field_view_map = {}
        for field in state.field_list:
            field_view_map[field.id] = await view_registry.resolve(locale, field.view)
        object = FormObject.from_state({id: view.get_object() for id, view in field_view_map.items()}, state.object)
        return cls(parent, object, field_view_map)

    def __init__(self, parent, object, field_view_map):
        super().__init__(parent)
        self._object = object


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(services)
        #services.objimpl_registry.register(FormObject.impl_id, FormObject.from_state)
        services.view_registry.register(FormView.impl_id, FormView.from_state, services.objimpl_registry, services.view_registry)
