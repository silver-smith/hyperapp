import os.path
import iface_registry
from list_obj import ListObj


class RefList(ListObj):

    def run_command( self, command_id ):
        if command_id == 'add':
            return self.run_command_add()
        return ListObj.run_command(self, command_id)

    def run_command_add( self ):
        request = dict(self.make_command_request(command_id='add'),
                       target_path=self.get_default_ref())
        return self.server.request_an_object(request)

    # todo
    def get_default_ref( self ):
        return dict(
            module='file',
            fspath=os.path.expanduser('~'))


iface_registry.register_iface('ref_list', RefList.from_resp)
