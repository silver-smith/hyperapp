from . import htypes
from .services import (
    mosaic,
    )
from .code.rc_resource import Resource


class ConfigItemResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name, piece.config_item)

    def __init__(self, service_name, template_ref):
        self._service_name = service_name
        self._template_ref = template_ref

    @property
    def piece(self):
        return htypes.config_item_resource.config_item_resource(
            service_name=self._service_name,
            config_item=self._template_ref,
            )

    @property
    def is_config_ctl_creg_item(self):
        return self._service_name == 'config_ctl_creg'

    @property
    def is_system_resource(self):
        return self._service_name == 'system'

    def configure_system(self, system):
        # Should use cfg_item_creg from system probe
        # so that missing actors from config probe can be caught.
        cfg_item_creg = system.resolve_service('cfg_item_creg')
        template = cfg_item_creg.invite(self._template_ref)
        system.update_config(self._service_name, {template.key: template})
