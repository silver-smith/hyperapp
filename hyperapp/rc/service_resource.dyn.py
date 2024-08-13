from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.rc_requirement import Requirement
from .code.rc_resource import Resource


class ServiceReq(Requirement):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg):
        return cls(piece.service_name, cfg_item_creg)

    def __init__(self, service_name, cfg_item_creg):
        self._service_name = service_name
        self._cfg_item_creg = cfg_item_creg

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
        cfg_item = self._cfg_item_creg.animate(template_piece, self._service_name)
        return ServiceTemplateResource(
            service_name=self._service_name,
            cfg_item=cfg_item,
            )


class ServiceTemplateResource(Resource):

    @classmethod
    def from_piece(cls, piece, cfg_item_creg):
        cfg_item = cfg_item_creg.invite(piece.template, piece.service_name)
        return cls(piece.service_name, cfg_item)

    def __init__(self, service_name, cfg_item):
        self._service_name = service_name
        self._cfg_item = cfg_item

    @property
    def piece(self):
        return htypes.service_resource.service_template_resource(
            service_name=self._service_name,
            template=mosaic.put(self._cfg_item.piece),
            )

    def configure_system(self, system):
        system.update_config('system', {self._cfg_item.key: self._cfg_item.value})
