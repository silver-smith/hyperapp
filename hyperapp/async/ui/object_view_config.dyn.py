from hyperapp.common.module import Module

from . import htypes


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.view_dir_to_config[(htypes.object.object_d(),)] = self.config_editor_for_object

    def config_editor_for_object(self, piece):
        assert 0, 'todo'
