from . import htypes
from .services import (
    web,
    )
from .code.rc_resource import Resource


class ConfigItemResourceBase(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, piece.config_item)

    def __init__(self, service_name, cfg_item_ref):
        self._service_name = service_name
        self._cfg_item_ref = cfg_item_ref

    def __eq__(self, rhs):
        return (
            self.__class__ is rhs.__class__
            and self._service_name == rhs._service_name
            and self._cfg_item_ref == rhs._cfg_item_ref
            )

    def __hash__(self):
        return hash(('config-item-resource', self._service_name, self._cfg_item_ref))

    @property
    def is_system_resource(self):
        return self._service_name in {'config_ctl_creg', 'cfg_item_creg', 'cfg_value_creg'}

    @property
    def is_service_resource(self):
        return self._service_name == 'system'


class ConfigItemResource(ConfigItemResourceBase):

    @property
    def piece(self):
        return htypes.config_item_resource.config_item_resource(
            service_name=self._service_name,
            config_item=self._cfg_item_ref,
            )

    @property
    def system_config_items(self):
        item = web.summon(self._cfg_item_ref)
        return {self._service_name: [item]}


class ConfigItemResourceOverride(ConfigItemResourceBase):

    @property
    def piece(self):
        return htypes.config_item_resource.config_item_resource_override(
            service_name=self._service_name,
            config_item=self._cfg_item_ref,
            )

    @property
    def system_config_items_override(self):
        item = web.summon(self._cfg_item_ref)
        return {self._service_name: [item]}
