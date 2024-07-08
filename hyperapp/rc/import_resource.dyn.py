from . import htypes
from .services import (
    mosaic,
    web,
    )


class ImportResource:

    @classmethod
    def from_type_src(cls, type_src):
        import_name = ['htypes', type_src.module_name, type_src.name]
        return cls(import_name, type_src.type_piece)

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.import_name, web.summon(piece.resource))

    def __init__(self, import_name, resource):
        self._import_name = import_name
        self._resource = resource

    @property
    def piece(self):
        return htypes.import_resource.import_resource(
            import_name=tuple(self._import_name),
            resource=mosaic.put(self._resource),
            )

    @property
    def import_records(self):
        return [htypes.builtin.import_rec(
            full_name='.'.join(self._import_name),
            resource=mosaic.put(self._resource),
            )]
