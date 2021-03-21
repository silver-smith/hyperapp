# load&save client application state from/to file

from pathlib import Path
import logging

from hyperapp.common.htypes.packet_coders import DecodeError, packet_coders
from hyperapp.common.module import Module

from . import htypes
from .file_bundle import save_bundle_to_file, load_bundle_from_file

log = logging.getLogger(__name__)


STATE_FILE_PATH = Path('~/.local/share/hyperapp/client/state.json').expanduser()


class ApplicationStateStorage(object):

    def __init__(self, mosaic, ref_collector, unbundler):
        self._mosaic = mosaic
        self._ref_collector = ref_collector
        self._unbundler = unbundler

    @property
    def state_t(self):
        return htypes.application_state.application_state
        
    def save_state(self, state):
        state_ref = self._mosaic.put(state, htypes.application_state.application_state)
        bundle = self._ref_collector([state_ref]).bundle
        save_bundle_to_file(bundle, STATE_FILE_PATH)

    def load_state(self):
        try:
            bundle = load_bundle_from_file(STATE_FILE_PATH)
            self._unbundler.register_bundle(bundle)
            assert len(bundle.roots) == 1
            state_ref = bundle.roots[0]
            return self._mosaic.resolve_ref(state_ref).value
        except (FileNotFoundError, DecodeError) as x:
            log.info('Error loading %s: %r', STATE_FILE_PATH, x)
            return None
        

class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.application_state_storage = ApplicationStateStorage(
            services.mosaic, services.ref_collector, services.unbundler)
