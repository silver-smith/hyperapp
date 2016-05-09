# text object representing server text object

from ..common.htypes import tString
from .text_object import TextObject
from .proxy_object import ProxyObject
from .proxy_registry import proxy_class_registry


class ProxyTextObject(ProxyObject, TextObject):

    def __init__( self, server, path, iface, facets=None ):
        TextObject.__init__(self, text='')
        ProxyObject.__init__(self, server, path, iface, facets)
        self.text = self._load_text_from_cache()

    @staticmethod
    def get_objimpl_id():
        return 'proxy.text'

    def set_contents( self, contents ):
        ProxyObject.set_contents(self, contents)
        self.text = contents.text
        self._store_text_to_cache()

    def get_module_ids( self ):
        return [this_module_id]

    def get_commands( self, mode ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        commands = []
        for cmd in ProxyObject.get_commands(self):
            if mode is self.mode_view and cmd.id in ['view', 'save']: continue
            if mode is self.mode_edit and cmd.id in ['edit']: continue
            commands.append(cmd)
        return commands

    def run_command( self, command_id, initiator_view=None, **kw ):
        if command_id == 'edit' or command_id == 'view':
            return TextObject.run_command(self, command_id, initiator_view, **kw)
        if command_id == 'save':
            return ProxyObject.run_command(self, command_id, initiator_view, text=self.text, **kw)
        return ProxyObject.run_command(self, command_id, initiator_view, **kw)

    def process_response_result( self, command_id, result ):
        if command_id == 'save':
            self.path = result.new_path
            self._notify_object_changed()
        else:
            ProxyObject.process_response_result(self, command_id, result)

    def process_update( self, new_text ):
        self.text_changed(new_text)

    def _get_text_cache_key( self ):
        return self.make_cache_key('text')

    def _get_text_cache_type( self ):
        return tString

    def _store_text_to_cache( self ):
        key = self._get_text_cache_key()
        self.cache.store_value(key, self.text, self._get_text_cache_type())

    def _load_text_from_cache( self ):
        key = self._get_text_cache_key()
        return self.cache.load_value(key, self._get_text_cache_type())


proxy_class_registry.register(ProxyTextObject)
