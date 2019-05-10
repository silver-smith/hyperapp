# load&save client application state from/to file

from pathlib import Path
import logging

from hyperapp.common.htypes import TList
from hyperapp.common.htypes.packet_coders import DecodeError, packet_coders
from hyperapp.client.module import ClientModule
from . import htypes

log = logging.getLogger(__name__)


MODULE_NAME = 'application_state_storage'
STATE_FILE_PATH = Path('~/.local/share/hyperapp/client/state.json').expanduser()
STATE_FILE_ENCODING = 'json'


class ApplicationStateStorage(object):

    def __init__(self):
        self._state_type = TList(htypes.window.window_state)
        
    def save_state(self, state):
        STATE_FILE_PATH.write_bytes(packet_coders.encode(STATE_FILE_ENCODING, state, self._state_type))

    def load_state(self):
        try:
            data = STATE_FILE_PATH.read_bytes()
            return packet_coders.decode(STATE_FILE_ENCODING, data, self._state_type)
        except FileNotFoundError as x:
            log.info('Error loading %s: %r', STATE_FILE_PATH, x)
            return None


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.application_state_storage = ApplicationStateStorage()
