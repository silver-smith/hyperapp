from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.rc_resource import Resource
from .code.service_ctr import ServiceTemplateCtr


class ServiceTemplateResource(Resource):

    @classmethod
    def from_template(cls, service_name, template):
        return cls(
            module_name=template.module_name,
            attr_name=template.attr_name,
            service_name=service_name,
            free_params=template.free_params,
            service_params=template.service_params,
            want_config=template.want_config,
            )
            
    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_name=piece.attr_name,
            service_name=piece.service_name,
            free_params=piece.free_params,
            service_params=piece.service_params,
            want_config=piece.want_config,
            )

    def __init__(self, module_name, attr_name, service_name, free_params, service_params, want_config):
        self._module_name = module_name
        self._attr_name = attr_name
        self._service_name = service_name
        self._free_params = free_params
        self._service_params = service_params
        self._want_config = want_config

    @property
    def piece(self):
        return htypes.service_resource.service_template_resource(
            module_name=self._module_name,
            attr_name=self._attr_name,
            service_name=self._service_name,
            free_params=tuple(self._free_params),
            service_params=tuple(self._service_params),
            want_config=self._want_config,
            )

    def update_targets(self, target_factory):
        resource_tgt = target_factory.python_module_resource_by_module_name(self._module_name)
        ctr = ServiceTemplateCtr(
            attr_name=self._attr_name,
            name=self._service_name,
            free_params=self._free_params,
            service_params=self._service_params,
            want_config=self._want_config,
            )
        resource_tgt.add_component(ctr)
