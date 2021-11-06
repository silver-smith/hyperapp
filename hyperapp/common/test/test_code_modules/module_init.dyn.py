print("Module init (%s)" % __name__)


class ThisModule:

    def __init__(self, module_name, services, config):
        self.value = config['value']
