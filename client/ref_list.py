import os.path
import proxy_registry
from proxy_object import ProxyListObject


class RefList(ProxyListObject):

    def run_command( self, initiator_view, command_id ):
        if command_id == 'add':
            return self.run_command_add(initiator_view)
        return ProxyListObject.run_command(self, initiator_view, command_id)

    def run_command_add( self, initiator_view ):
        self.execute_command_request(initiator_view, 'add', target_path=self.get_default_ref())

    # todo
    def get_default_ref( self ):
        return dict(
            module='file',
            fspath=os.path.expanduser('~'))


proxy_registry.register_iface('ref_list', RefList.from_resp)
