from dataclasses import dataclass

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.rc_requirement import Requirement
from .code.rc_resource import Resource
from .code.system import ServiceTemplate


@dataclass(frozen=True, unsafe_hash=True)
class ServiceReq(Requirement):

    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name)

    @property
    def piece(self):
        return htypes.service_resource.service_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.config_item_complete('system', self.service_name)

    def make_resource(self, target):
        resource_tgt = target.provider_resource_tgt
        template_piece = resource_tgt.get_resource(target.constructor)
        return ServiceTemplateResource(
            service_name=self.service_name,
            template=ServiceTemplate.from_piece(template_piece),
            )


class ServiceTemplateResource(Resource):

    @classmethod
    def from_piece(cls, piece):
        template = ServiceTemplate.from_piece(piece.template)
        return cls(piece.service_name, template)

    def __init__(self, service_name, template):
        self._service_name = service_name
        self._template = template  # ServiceTemplate

    @property
    def piece(self):
        return htypes.service_resource.service_template_resource(
            service_name=self._service_name,
            template=self._template.piece,
            )

    @property
    def config_triplets(self):
        return [('system', self._service_name, self._template)]
