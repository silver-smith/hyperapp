print("Module init (%s)" % __name__)


class ThisModule:

    def __init__(self, module_name, services, config):
        self.value = config['value']
        self.phased_value = config['value']

    def some_method(self):
        return 456

    def init_phase_1(self, services):
        self.phased_value += 1

    def init_phase_3(self, services):
        self.phased_value += 1
