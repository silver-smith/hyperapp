
class Constructor:

    @property
    def is_fixture(self):
        return False

    def update_fixtures_targets(self, import_tgt, target_set):
        pass

    def update_targets(self, target_set):
        pass

    def update_resource_targets(self, resource_tgt, target_set):
        pass

    def make_component(self, types, python_module, name_to_res=None):
        raise NotImplementedError(self)

    def get_component(self, name_to_res):
        raise NotImplementedError(self)

    def make_resource(self, types, module_name, python_module):
        pass


class ModuleCtr(Constructor):

    def __init__(self, module_name):
        self._module_name = module_name

    def update_targets(self, target_set):
        resource_tgt = target_set.factory.python_module_resource_by_module_name(self._module_name)
        self.update_resource_targets(resource_tgt, target_set)

    def update_resource_targets(self, resource_tgt, target_set):
        raise NotImplementedError(self)
