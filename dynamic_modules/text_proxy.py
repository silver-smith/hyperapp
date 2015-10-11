# text object representing server text object

from .text_object import TextObject
from .proxy_object import ProxyObject
from .proxy_registry import proxy_registry


class ProxyTextObject(ProxyObject, TextObject):

    def __init__( self, server, path, iface ):
        TextObject.__init__(self, text='')
        ProxyObject.__init__(self, server, path, iface)

    @staticmethod
    def get_proxy_id():
        return 'text'

    def set_contents( self, contents ):
        ProxyObject.set_contents(self, contents)
        self.text = contents.text

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


proxy_registry.register_class(ProxyTextObject)
