import logging

from ..common.util import full_type_name_to_str
from ..common.htypes import Type, ref_t, capsule_t
from ..common.ref import ref_repr, decode_capsule
from ..common.htypes.packet_coders import packet_coders

log = logging.getLogger(__name__)


class UnknownRegistryIdError(KeyError):
    pass


class Registry(object):

    class _Rec(object):

        def __init__(self, factory, args, kw):
            self.factory = factory  # factory functon
            self.args = args
            self.kw = kw

    def __init__(self):
        self._registry = {}  # id -> _Rec

    def id_to_str(self, id):
        return repr(id)

    def register(self, id, factory, *args, **kw):
        log.debug('%s: registering %s -> %s(*%r, **%r)', self.__class__.__name__, self.id_to_str(id), factory, args, kw)
        assert id not in self._registry, repr(id)  # Duplicate id
        self._registry[id] = self._Rec(factory, args, kw)

    def is_registered(self, id):
        return id in self._registry

    def _resolve(self, id):
        try:
            return self._registry[id]
        except KeyError:
            raise UnknownRegistryIdError('Unknown id: %s' % repr(id))


class CapsuleRegistry(Registry):

    def __init__(self, produce_name, types):
        super().__init__()
        self._produce_name = produce_name
        self._types = types

    @property
    def produce_name(self):
        return self._produce_name

    def id_to_str(self, id):
        return full_type_name_to_str(id)

    def register(self, t, factory, *args, **kw):
        assert isinstance(t, Type), repr(t)
        assert t.full_name, repr(t)  # type must have a name
        super().register(tuple(t.full_name), factory, *args, **kw)

    def resolve(self, ref, capsule):
        assert isinstance(capsule, capsule_t), repr(capsule)
        object = decode_capsule(self._types, capsule)
        rec = self._resolve(tuple(capsule.full_type_name))
        log.info('producing %s %s for %s using %s(%s, %s) for object %r',
                     self._produce_name, ref_repr(ref), full_type_name_to_str(capsule.full_type_name), rec.factory, rec.args, rec.kw, object)
        return rec.factory(ref, object, *rec.args, **rec.kw)


class CapsuleResolver(object):

    def __init__(self, ref_resolver, capsule_registry):
        self._ref_resolver = ref_resolver
        self._capsule_registry = capsule_registry

    def resolve(self, ref):
        assert isinstance(ref, ref_t), repr(ref)
        capsule = self._ref_resolver.resolve_ref(ref)
        produce = self._capsule_registry.resolve(ref, capsule)
        assert produce, repr(produce)
        log.debug('Capsule %s is resolved to %s %r', ref_repr(ref), self._capsule_registry.produce_name, produce)
        return produce
