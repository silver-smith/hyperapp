from pathlib import Path

from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.work_dir = Path.home() / '.cache' / 'hyperapp' / 'server'
