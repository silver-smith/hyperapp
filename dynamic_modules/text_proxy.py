# text object representing server text object

from ..common.htypes import tString
from .command import command
from .text_object import TextObject
from .proxy_object import ProxyObject


def register_object_implementations(registry, services):
    ProxyTextObject.register(registry, services)


class ProxyTextObject(ProxyObject, TextObject):

    impl_id = 'proxy.text'

    def __init__( self, packet_types, core_types, iface_registry, cache_repository,
                  resources_manager, param_editor_registry, server, path, iface, facets=None ):
        TextObject.__init__(self, text='')
        ProxyObject.__init__(self, packet_types, core_types, iface_registry, cache_repository,
                             resources_manager, param_editor_registry, server, path, iface, facets)
        self.text = self._load_text_from_cache()

    def set_contents(self, contents):
        ProxyObject.set_contents(self, contents)
        self.text = contents.text
        self._store_text_to_cache()

    def get_commands(self, mode):
        assert mode in self.Mode, repr(mode)
        return self.filter_mode_commands(ProxyObject.get_commands(self), mode)

    def command_must_be_visible_for_mode(self, command, mode):
        if mode is self.Mode.VIEW and command.id == 'save':
            return False
        return TextObject.command_must_be_visible_for_mode(self, command, mode)
    
    @command('save')
    async def command_save(self):
        result = await self.execute_request('save', text=self.text)
        self.path = result.new_path
        self._notify_object_changed()

    async def open_ref(self, ref_id):
        result = await self.execute_request('open_ref', ref_id=ref_id)
        return result.handle
        
    def process_diff(self, new_text):
        self.text_changed(new_text)

    def _get_text_cache_key(self):
        return self.make_cache_key('text')

    def _get_text_cache_type(self):
        return tString

    def _store_text_to_cache(self):
        key = self._get_text_cache_key()
        self.cache_repository.store_value(key, self.text, self._get_text_cache_type())

    def _load_text_from_cache(self):
        key = self._get_text_cache_key()
        return self.cache_repository.load_value(key, self._get_text_cache_type())
