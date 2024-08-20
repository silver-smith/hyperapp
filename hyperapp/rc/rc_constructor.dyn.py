
class Constructor:

    @property
    def is_fixture(self):
        return False

    def update_resource_targets(self, resource_tgt, target_set):
        pass

    def update_fixtures_targets(self, import_alias_tgt, target_set):
        pass

    def update_targets(self, target_set):
        pass

    def make_component(self, python_module, name_to_res=None):
        raise NotImplementedError(self)

    def get_component(self, name_to_res):
        raise NotImplementedError(self)

    def make_resource(self, module_name, python_module):
        pass
