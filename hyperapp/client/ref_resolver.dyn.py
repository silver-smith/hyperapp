import logging

from ..common.interface import hyper_ref as href_types
from ..common.url import UrlWithRoutes
from ..common.packet_coders import packet_coders
from ..common.ref import make_piece, make_ref
from ..common.local_server_paths import LOCAL_REF_RESOLVER_REF_PATH, load_bundle_from_file
from .piece_registry import PieceRegistry, PieceResolver
from .module import Module

log = logging.getLogger(__name__)


class RefResolver(object):

    def __init__(self, type_registry_registry, ref_registry, ref_resolver_proxy):
        self._type_registry_registry = type_registry_registry
        self._ref_registry = ref_registry
        self._ref_resolver_proxy = ref_resolver_proxy

    async def resolve_ref(self, ref):
        piece = self._ref_registry.resolve(ref)
        if not piece:
            result = await self._ref_resolver_proxy.resolve_ref(ref)
            piece = result.piece
            self._ref_registry.register(ref, piece)
        log.debug('ref resolver: ref resolved to %r', piece)
        assert piece, repr(piece)
        return piece

    async def resolve_ref_to_object(self, ref):
        piece = await self.resolve_ref(ref)
        t = self._type_registry_registry.resolve_type(piece.full_type_name)
        return packet_coders.decode(piece.encoding, piece.encoded_object, t)


class RefRegistry(object):

    def __init__(self):
        self._registry = {}

    # check if piece is matching if ref is already registered
    def register(self, ref, piece):
        assert isinstance(ref, href_types.ref), repr(ref)
        assert isinstance(piece, href_types.piece), repr(piece)
        existing_piece = self._registry.get(ref)
        if existing_piece:
            assert piece == existing_piece, repr((existing_piece, piece))  # new piece does not match existing one
        self._registry[ref] = piece

    def register_new_object(self, t, object):
        piece = make_piece(t, object)
        ref = make_ref(piece)
        self.register(ref, piece)
        return ref

    def register_piece_list(self, piece_list):
        for piece in piece_list:
            ref = make_ref(piece)
            self.register(ref, piece)

    def resolve(self, ref):
        return self._registry.get(ref)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._remoting = services.remoting
        self._ref_registry = RefRegistry()
        bundle = load_bundle_from_file(LOCAL_REF_RESOLVER_REF_PATH)
        self._ref_registry.register_piece_list(bundle.piece_list)

        with open(url_path) as f:
            url = UrlWithRoutes.from_str(services.iface_registry, f.read())
        ref_resolver_proxy = services.proxy_factory.from_url(url)
        services.ref_registry = self._ref_registry
        services.ref_resolver = ref_resolver = RefResolver(services.type_registry_registry, self._ref_registry, ref_resolver_proxy)
        services.handle_registry = handle_registry = PieceRegistry('handle', services.type_registry_registry)
        services.handle_resolver = PieceResolver(ref_resolver, handle_registry)
