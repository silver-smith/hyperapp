

class CtrCollector:

    def __init__(self, config):
        self._pyname_to_hname = {
            module.__name__: name
            for name, module in config.items()
            }
        self._constructors = []

    def get_module_name(self, python_module_name):
        return self._pyname_to_hname.get(python_module_name)

    def add_constructor(self, ctr):
        self._constructors.append(ctr)

    @property
    def constructors(self):
        return self._constructors


def ctr_collector(config):
    return CtrCollector(config)
