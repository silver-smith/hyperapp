import logging

from ..common.htypes import Type
from ..common.packet_coders import packet_coders
from .registry import Registry

log = logging.getLogger(__name__)



class ReferredRegistry(Registry):

    def __init__(self, produce_name, type_registry_registry):
        super().__init__()
        self._produce_name = produce_name
        self._type_registry_registry = type_registry_registry

    def register(self, t, factory, *args, **kw):
        assert isinstance(t, Type), repr(t)
        assert t.full_name, repr(t)  # type must have a name
        super().register(tuple(t.full_name), factory, *args, **kw)
        
    async def resolve(self, referred):
        t = self._type_registry_registry.resolve_type(referred.full_type_name)
        object = packet_coders.decode(referred.encoding, referred.encoded_object, t)
        rec = self._resolve(tuple(referred.full_type_name))
        log.info('producing %s for %s using %s(%s, %s) for object %r',
                     self._produce_name, '.'.join(referred.full_type_name), rec.factory, rec.args, rec.kw, object)
        return (await rec.factory(object, *rec.args, **rec.kw))
