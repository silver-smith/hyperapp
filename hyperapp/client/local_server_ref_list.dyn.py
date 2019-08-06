import os.path

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from .local_server_paths import LOCAL_SERVER_DYNAMIC_REF_LIST_REF_PATH, load_bundle_from_file


MODULE_NAME = 'local_server_ref_list'


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        ref = self._load_local_server_ref(services.unbundler)
        self._local_server_ref_list = services.type_resolver.resolve_ref(ref).value

    @command('open_local_server')
    async def open_local_server(self):
        return self._local_server_ref_list

    def _load_local_server_ref(self, unbundler):
        bundle = load_bundle_from_file(LOCAL_SERVER_DYNAMIC_REF_LIST_REF_PATH)
        unbundler.register_bundle(bundle)
        assert len(bundle.roots) == 1
        return bundle.roots[0]
