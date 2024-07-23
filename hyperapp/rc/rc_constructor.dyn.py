
class Constructor:

    def update_targets(self, resource_target, target_factory):
        pass

    def update_tests_targets(self, import_alias_tgt, target_set):
        pass

    def make_component(self, python_module, name_to_res=None):
        raise NotImplementedError(self)

    def get_component(self, name_to_res):
        raise NotImplementedError(self)

    def make_resource(self, python_module):
        pass
