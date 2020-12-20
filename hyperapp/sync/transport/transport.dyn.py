from hyperapp.common.module import Module


class Transport:

    def send(self, parcel):
        assert 0, 'todo'


class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        services.transport = Transport()
