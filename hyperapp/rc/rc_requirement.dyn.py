
class Requirement:

    @property
    def is_test_requirement(self):
        return False

    def update_tested_target(self, import_target, test_target, target_set):
        return None
