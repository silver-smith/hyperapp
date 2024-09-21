from . import htypes
from .services import mosaic
from .code.rc_requirement import Requirement
from .code.config_item_resource import ConfigItemResource


class ServiceReq(Requirement):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg):
        return cls(piece.service_name, cfg_item_creg)

    def __init__(self, service_name, cfg_item_creg):
        self._service_name = service_name
        self._cfg_item_creg = cfg_item_creg

    def __str__(self):
        return f"ServiceReq(service_name={self._service_name})"

    def __eq__(self, rhs):
        return type(rhs) == ServiceReq and rhs._service_name == self._service_name

    def __hash__(self):
        return hash(('service_req', self._service_name))

    @property
    def piece(self):
        return htypes.service_resource.service_req(self._service_name)

    def get_target(self, target_factory):
        return target_factory.config_item_complete('system', self._service_name)

    def make_resource(self, target):
        resource_tgt = target.provider_resource_tgt
        template_piece = resource_tgt.get_resource(target.constructor)
        return ConfigItemResource(
            cfg_item_creg=self._cfg_item_creg,
            service_name='system',
            template_ref=mosaic.put(template_piece),
            )
