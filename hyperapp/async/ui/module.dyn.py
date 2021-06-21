import weakref

from hyperapp.common.module import Module


# decorator for module methods
class global_command:

    def __init__(self, id):
        self.id = id

    def __call__(self, method):
        return UnboundCommand(self.id, method)


class UnboundCommand:

    def __init__(self, id, method):
        self.id = id
        self._method = method

    def bind(self, instance):
        instance_wr = weakref.ref(instance)
        return BoundCommand(self.id, self._method, instance_wr)


class BoundCommand:

    def __init__(self, id, method, instance_wr):
        self.id = id
        self._method = method
        self._instance_wr = instance_wr

    def __repr__(self):
        return f"Global:{self.id}@{self._instance_wr()}"

    async def run(self):
        instance = self._instance_wr()
        if instance is None:
            return  # Instance already destroyed.
        return await self._method(instance)


class ClientModule(Module):

    def __init__(self, name, services, config):
        super().__init__(name, services, config)
        for name in dir(self):
            attr = getattr(self, name)
            if type(attr) is property:
                continue
            if not isinstance(attr, UnboundCommand):
                continue
            this_module.global_command_list.append(attr.bind(self))


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self.global_command_list = []
        services.global_command_list = self.global_command_list
