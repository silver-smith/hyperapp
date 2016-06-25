import os.path
import asyncio
from .proxy_list_object import ProxyListObject


def register_object_implementations( registry, services ):
    RefList.register(registry, services)


class RefList(ProxyListObject):

    objimpl_id = 'ref_list'

    @asyncio.coroutine
    def run_command( self, command_id=None, **kw ):
        if command_id == 'add':
            return (yield from self.run_command_add())
        return (yield from ProxyListObject.run_command(self, command_id, **kw))

    @asyncio.coroutine
    def run_command_add( self ):
        return (yield from self.execute_request('add', target_url=self.get_default_url().to_data()))

    # todo
    def get_default_url( self ):
        iface = self.iface_registry.resolve('fs_dir')
        return self.server.make_url(iface, ['file', os.path.expanduser('~')])
