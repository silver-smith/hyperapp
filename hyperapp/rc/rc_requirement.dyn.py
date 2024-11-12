
class Requirement:

    @property
    def desc(self):
        return None

    @property
    def is_test_requirement(self):
        return False

    def update_tested_target(self, import_target, test_target, target_set):
        pass

    def make_resource_list(self, target):
        resource = self.make_resource(target)
        return [resource]
