from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.rc_resource import Resource


class ConfigItemResourceBase(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, piece.config_item)

    def __init__(self, service_name, template_ref):
        self._service_name = service_name
        self._template_ref = template_ref

    @property
    def is_system_resource(self):
        return self._service_name in {'config_ctl_creg', 'cfg_item_creg'}

    @property
    def is_service_resource(self):
        return self._service_name == 'system'


class ConfigItemResource(ConfigItemResourceBase):

    @property
    def piece(self):
        return htypes.config_item_resource.config_item_resource(
            service_name=self._service_name,
            config_item=self._template_ref,
            )

    @property
    def system_config_items(self):
        item = web.summon(self._template_ref)
        return {self._service_name: [item]}


class ConfigItemResourceOverride(ConfigItemResourceBase):

    @property
    def piece(self):
        return htypes.config_item_resource.config_item_resource_override(
            service_name=self._service_name,
            config_item=self._template_ref,
            )

    @property
    def system_config_items_override(self):
        item = web.summon(self._template_ref)
        return {self._service_name: [item]}
