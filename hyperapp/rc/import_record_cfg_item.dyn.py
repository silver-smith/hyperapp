from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )


class ImportRecordCfgItem:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            import_name=piece.import_name,
            resource=web.summon(piece.resource),
            )

    def __init__(self, module_name, import_name, resource):
        self._module_name = module_name
        self._import_name = tuple(import_name)
        self._resource = resource

    @property
    def piece(self):
        return htypes.import_resource.import_resource(
            module_name=self._module_name,
            import_name=self._import_name,
            resource=mosaic.put(self._resource),
            )

    @property
    def key(self):
        return (self._module_name, self._import_name)

    def resolve(self, system, service_name):
        return self._resource
