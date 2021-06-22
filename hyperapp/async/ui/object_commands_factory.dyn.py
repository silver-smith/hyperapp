from hyperapp.common.module import Module


class ObjectCommandsFactory:

    def get_object_command_list(self, object):
        return object.command_list


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_commands_factory = ObjectCommandsFactory()
