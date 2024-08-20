

class CtrCollector:

    def __init__(self, config):
        self._module_to_name = {
            module: name
            for name, module in config.items()
            }
        self._constructors = []

    def get_module_name(self, module):
        return self._module_to_name.get(module)

    def add_constructor(self, ctr):
        self._constructors.append(ctr)


def ctr_collector(config):
    return CtrCollector(config)
