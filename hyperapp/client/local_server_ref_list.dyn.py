import os.path

from ..common.interface import hyper_ref as href_types
from ..common.local_server_paths import LOCAL_SERVER_REF_LIST_REF_PATH
from .command import command
from .module import ClientModule


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(services)
        self._handle_resolver = services.handle_resolver
        ref_path = os.path.expanduser(LOCAL_SERVER_REF_LIST_REF_PATH)
        with open(ref_path, 'rb') as f:
            self._server_ref_list_ref = f.read()

    @command('open_local_server')
    async def open_local_server(self):
        return (await self._handle_resolver.resolve(self._server_ref_list_ref))
