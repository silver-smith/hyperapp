# load&save client application state from/to file

from pathlib import Path
import logging

from hyperapp.common.htypes import TList, t_ref, t_list_meta, meta_ref_t
from hyperapp.common.htypes.packet_coders import DecodeError, packet_coders
from hyperapp.client.module import ClientModule
from . import htypes
from .local_server_paths import save_bundle_to_file, load_bundle_from_file

log = logging.getLogger(__name__)

STATE_FILE_PATH = Path('~/.local/share/hyperapp/client/state.json').expanduser()


class ApplicationStateStorage(object):

    def __init__(self, type_resolver, ref_registry, ref_collector_factory, unbundler):
        self._type_resolver = type_resolver
        self._ref_registry = ref_registry
        self._ref_collector_factory = ref_collector_factory
        self._unbundler = unbundler
        self._state_type = self._register_state_type()
        
    def save_state(self, state):
        state_ref = self._ref_registry.register_object(state, self._state_type)
        ref_collector = self._ref_collector_factory()
        bundle = ref_collector.make_bundle([state_ref])
        save_bundle_to_file(bundle, STATE_FILE_PATH)

    def load_state(self):
        try:
            bundle = load_bundle_from_file(STATE_FILE_PATH)
            self._unbundler.register_bundle(bundle)
            assert len(bundle.roots) == 1
            state_ref = bundle.roots[0]
            return self._type_resolver.resolve_ref(state_ref).value
        except (FileNotFoundError, DecodeError) as x:
            log.info('Error loading %s: %r', STATE_FILE_PATH, x)
            return None

    def _register_state_type(self):
        window_state_ref = self._type_resolver.reverse_resolve(htypes.window.window)
        type_rec = meta_ref_t('application_state', t_list_meta(t_ref(window_state_ref)))
        return self._type_resolver.register_type(self._ref_registry, type_rec).t
        

class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.application_state_storage = ApplicationStateStorage(
            services.type_resolver, services.ref_registry, services.ref_collector_factory, services.unbundler)
