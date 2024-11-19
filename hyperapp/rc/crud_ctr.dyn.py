from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import ModuleCtr


class CrudTemplateCtr(ModuleCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            action=piece.action,
            crud_params=piece.crud_params,
            service_params=piece.service_params,
            )

    def __init__(self, module_name, attr_qual_name, action, crud_params, service_params):
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._action = action
        self._crud_params = crud_params
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.crud.crud_template_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            action=self._action,
            crud_params=tuple(self._crud_params),
            service_params=tuple(self._service_params),
            )

    def get_component(self, name_to_res):
        return name_to_res[f'{self._resource_name}.actor-template']

    @property
    def _type_name(self):
        return f'{self._t.module_name}_{self._t.name}'

    @property
    def _resource_name(self):
        return f'{self._type_name}-{self._action}'
