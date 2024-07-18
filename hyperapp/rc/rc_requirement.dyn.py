
class Requirement:

    @property
    def is_test_requirement(self):
        return False

    def get_tested_resource_target(self, target, target_factory):
        return None
