from .object_command import command
from .module import ClientModule


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._local_server_ref = services.local_server_ref

    @command('open_local_server')
    async def open_local_server(self):
        return self._local_server_ref.load_piece()
