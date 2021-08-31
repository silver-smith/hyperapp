# load&save client application state from/to file

from pathlib import Path
import logging

from hyperapp.common.htypes.packet_coders import DecodeError
from hyperapp.common.module import Module

log = logging.getLogger(__name__)


STATE_FILE_PATH = Path('~/.local/share/hyperapp/client/state.json').expanduser()


class ApplicationStateStorage(object):

    def __init__(self, file_bundle):
        self._file_bundle = file_bundle
        
    def save_state(self, state):
        self._file_bundle.save_piece(state)

    def load_state(self):
        try:
            return self._file_bundle.load_piece()
        except (FileNotFoundError, DecodeError) as x:
            log.info('Error loading %s: %r', self._file_bundle.path, x)
            return None
        

class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        file_bundle = services.file_bundle(STATE_FILE_PATH)
        services.application_state_storage = ApplicationStateStorage(file_bundle)
