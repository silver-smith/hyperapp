import os.path
import proxy_registry
from proxy_object import ProxyListObject


class RefList(ProxyListObject):

    def run_command( self, initiator_view, command_id ):
        if command_id == 'add':
            return self.run_command_add()
        return ProxyListObject.run_command(self, initiator_view, command_id)

    def run_command_add( self ):
        request = dict(self.make_command_request(command_id='add'),
                       target_path=self.get_default_ref())
        return self.server.request_an_object(request)

    # todo
    def get_default_ref( self ):
        return dict(
            module='file',
            fspath=os.path.expanduser('~'))


proxy_registry.register_iface('ref_list', RefList.from_resp)
