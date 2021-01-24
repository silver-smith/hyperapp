from hyperapp.common.module import Module


class RpcEndpoint:

    def process(self, request):
        raise NotImplementedError('todo')


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
