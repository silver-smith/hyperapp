import codecs
import logging
from pathlib import Path

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.client.module import ClientModule

from . import htypes

_log = logging.getLogger(__name__)


ASSOCIATION_DIR = Path('~/.local/share/hyperapp/client/object-layout-association').expanduser()


class ObjectLayoutAssociationRepository:

    def __init__(self, ref_registry, object_layout_resolver, dir):
        self._ref_registry = ref_registry
        self._object_layout_resolver = object_layout_resolver
        self._dir = dir

    def associate(self, object_type, layout):
        _log.info("Associate object type %s with layout %s", object_type, layout.data)
        object_type_ref = self._ref_registry.register_object(object_type)
        layout_ref = self._ref_registry.register_object(layout.data)
        record = htypes.object_layout_association.repository_record(object_type_ref, layout_ref)
        data = packet_coders.encode('yaml', record)
        path = self._file_path(object_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def resolve(self, object_type, layout_watcher):
        _log.info("Resolve association of object type %s:", object_type)
        path = self._file_path(object_type)
        if not path.exists():
            _log.info("Resolve association of object type %s: None found", object_type)
            return None
        data = path.read_bytes()
        record = packet_coders.decode('yaml', data, htypes.object_layout_association.repository_record)
        layout = await self._object_layout_resolver.resolve(record.layout_ref, ['root'], layout_watcher)
        _log.info("Resolve association of object type %s: found %s", object_type, layout.data)
        return layout

    def _file_path(self, object_type):
        object_type_ref = self._ref_registry.register_object(object_type)
        hash_hex = codecs.encode(object_type_ref.hash[:4], 'hex').decode()
        return self._dir / f'{object_type._t.name}-{object_type_ref.hash_algorithm}:{hash_hex}.yaml'


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_layout_association = ObjectLayoutAssociationRepository(
            services.ref_registry, services.object_layout_resolver, ASSOCIATION_DIR)
