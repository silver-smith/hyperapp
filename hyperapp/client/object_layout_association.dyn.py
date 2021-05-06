import codecs
import logging
from pathlib import Path

from hyperapp.common.htypes.packet_coders import packet_coders

from . import htypes
from .module import ClientModule

_log = logging.getLogger(__name__)


ASSOCIATION_DIR = Path('~/.local/share/hyperapp/client/object-layout-association').expanduser()


class ObjectLayoutAssociationRepository:

    def __init__(self, mosaic, object_layout_registry, dir):
        self._mosaic = mosaic
        self._object_layout_registry = object_layout_registry
        self._dir = dir

    def associate_type(self, object_type, layout):
        _log.info("Associate object type %s with layout %s", object_type, layout.piece)
        object_type_ref = self._mosaic.put(object_type)
        layout_ref = self._mosaic.put(layout.piece)
        record = htypes.object_layout_association.type_repository_record(object_type_ref, layout_ref)
        data = packet_coders.encode('yaml', record)
        path = self._type_file_path(object_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def associate_command(self, origin_object_type, command_id, layout):
        _log.info("Associate object command %s/%s with layout %s", origin_object_type, command_id, layout.piece)
        origin_object_type_ref = self._mosaic.put(origin_object_type)
        layout_ref = self._mosaic.put(layout.piece)
        record = htypes.object_layout_association.command_repository_record(origin_object_type_ref, command_id, layout_ref)
        data = packet_coders.encode('yaml', record)
        path = self._command_file_path(origin_object_type, command_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def resolve_type(self, object_type, layout_watcher):
        _log.debug("Resolve association of object type %s:", object_type)
        path = self._type_file_path(object_type)
        if not path.exists():
            _log.info("Resolve association of object type %s: None found", object_type)
            return None
        data = path.read_bytes()
        record = packet_coders.decode('yaml', data, htypes.object_layout_association.type_repository_record)
        layout = await self._object_layout_registry.invite(record.layout_ref, ['root'], layout_watcher)
        _log.info("Resolve association of object type %s: found %s", object_type, layout.piece)
        return layout

    async def resolve_command(self, origin_object_type, command_id, layout_watcher):
        _log.debug("Resolve association of command %s/%s:", origin_object_type, command_id)
        path = self._command_file_path(origin_object_type, command_id)
        if not path.exists():
            _log.info("Resolve association of command %s/%s: None found", origin_object_type, command_id)
            return None
        data = path.read_bytes()
        record = packet_coders.decode('yaml', data, htypes.object_layout_association.command_repository_record)
        layout = await self._object_layout_registry.invite(record.layout_ref, ['root'], layout_watcher)
        _log.info("Resolve association of command %s/%s: found %s", origin_object_type, command_id, layout.piece)
        return layout

    def _type_file_path(self, object_type):
        object_type_ref = self._mosaic.put(object_type)
        hash_hex = codecs.encode(object_type_ref.hash[:4], 'hex').decode()
        return self._dir / f'{object_type._t.name}-{object_type_ref.hash_algorithm}:{hash_hex}.yaml'

    def _command_file_path(self, origin_object_type, command_id):
        origin_object_type_ref = self._mosaic.put(origin_object_type)
        hash_hex = codecs.encode(origin_object_type_ref.hash[:4], 'hex').decode()
        return self._dir / f'{origin_object_type._t.name}-{command_id}-{origin_object_type_ref.hash_algorithm}:{hash_hex}.yaml'


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_layout_association = ObjectLayoutAssociationRepository(
            services.mosaic, services.object_layout_registry, ASSOCIATION_DIR)
