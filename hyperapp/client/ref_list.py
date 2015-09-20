import os.path
from .proxy_registry import proxy_registry
from .proxy_list_object import ProxyListObject


class RefList(ProxyListObject):

    @staticmethod
    def get_proxy_id():
        return 'ref_list'

    def run_command( self, command_id, initiator_view=None, **kw ):
        if command_id == 'add':
            return self.run_command_add(initiator_view)
        return ProxyListObject.run_command(self, command_id, initiator_view, **kw)

    def run_command_add( self, initiator_view ):
        self.execute_request('add', initiator_view, target_path=self.get_default_ref())

    # todo
    def get_default_ref( self ):
        return ['file'] + os.path.expanduser('~').split('/')


proxy_registry.register_class(RefList)
