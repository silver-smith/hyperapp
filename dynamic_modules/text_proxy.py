# text object representing server text object

import asyncio
from ..common.htypes import tString
from .command import command
from .text_object import TextObject
from .proxy_object import ProxyObject


def register_object_implementations( registry, services ):
    ProxyTextObject.register(registry, services)


class ProxyTextObject(ProxyObject, TextObject):

    objimpl_id = 'proxy.text'

    def __init__( self, request_types, core_types, iface_registry, cache_repository, server, path, iface, facets=None ):
        TextObject.__init__(self, text='')
        ProxyObject.__init__(self, request_types, core_types, iface_registry, cache_repository, server, path, iface, facets)
        self.text = self._load_text_from_cache()

    def set_contents( self, contents ):
        ProxyObject.set_contents(self, contents)
        self.text = contents.text
        self._store_text_to_cache()

    def get_commands( self, mode ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        commands = ProxyObject.get_commands(self)
        def pred( command ):
            if mode is self.mode_view:
                return command.id not in ['view', 'save']
            if mode is self.mode_edit:
                return command.id not in ['edit']
        return list(filter(pred, commands))

    @command('save')
    @asyncio.coroutine
    def command_save( self ):
        result = yield from self.run_remote_command('save', text=self.text)
        self.path = result.new_path
        self._notify_object_changed()

    @asyncio.coroutine
    def open_ref( self, ref_id ):
        return (yield from self.run_remote_command('open_ref', ref_id=ref_id))
        
    def process_update( self, new_text ):
        self.text_changed(new_text)

    def _get_text_cache_key( self ):
        return self.make_cache_key('text')

    def _get_text_cache_type( self ):
        return tString

    def _store_text_to_cache( self ):
        key = self._get_text_cache_key()
        self.cache_repository.store_value(key, self.text, self._get_text_cache_type())

    def _load_text_from_cache( self ):
        key = self._get_text_cache_key()
        return self.cache_repository.load_value(key, self._get_text_cache_type())
