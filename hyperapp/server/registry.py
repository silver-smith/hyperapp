import logging

from ..common.interface import hyper_ref as href_types
from ..common.htypes import Type
from ..common.ref import decode_capsule
from ..common.packet_coders import packet_coders

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

    def register(self, id, factory, *args, **kw):
        log.debug('%s: registering %r -> %s(*%r, **%r)', self.__class__.__name__, id, factory, args, kw)
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

    def register(self, t, factory, *args, **kw):
        assert isinstance(t, Type), repr(t)
        assert t.full_name, repr(t)  # type must have a name
        super().register(tuple(t.full_name), factory, *args, **kw)

    def resolve(self, capsule):
        assert isinstance(capsule, href_types.capsule), repr(capsule)
        object = decode_capsule(self._types, capsule)
        rec = self._resolve(tuple(capsule.full_type_name))
        log.info('producing %s for %s using %s(%s, %s) for object %r',
                     self._produce_name, '.'.join(capsule.full_type_name), rec.factory, rec.args, rec.kw, object)
        return rec.factory(object, *rec.args, **rec.kw)


class CapsuleResolver(object):

    def __init__(self, ref_resolver, capsule_registry):
        self._ref_resolver = ref_resolver
        self._capsule_registry = capsule_registry

    def resolve(self, ref):
        assert isinstance(ref, bytes), repr(ref)
        capsule = self._ref_resolver.resolve_ref(ref)
        produce = self._capsule_registry.resolve(capsule)
        assert produce, repr(produce)
        log.debug('capsule resolved to %s %r', self._capsule_registry.produce_name, produce)
        return produce
