from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.rc_resource import Resource


class ImportResource(Resource):

    @classmethod
    def from_type_src(cls, module_name, type_src):
        import_name = ['htypes', type_src.module_name, type_src.name]
        return cls(module_name, import_name, type_src.type_piece)

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

    def __eq__(self, rhs):
        return (
            self.__class__ is rhs.__class__
            and self._module_name == rhs._module_name
            and self._import_name == rhs._import_name
            and self._resource == rhs._resource
            )

    def __hash__(self):
        return hash(('import-resource', self._module_name, self._import_name, self._resource))

    @property
    def piece(self):
        return htypes.import_resource.import_resource(
            module_name=self._module_name,
            import_name=self._import_name,
            resource=mosaic.put(self._resource),
            )

    @property
    def import_records(self):
        return [htypes.builtin.import_rec(
            full_name='.'.join(self._import_name),
            resource=mosaic.put(self._resource),
            )]

    @property
    def system_config_items(self):
        return {'import_recorder_reg': [self.piece]}
