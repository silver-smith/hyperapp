import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


def load_fixtures(resource_module, resource_type, module_dir_list):
    ext = '.fixture.py'
    for root_dir in module_dir_list:
        for path in root_dir.rglob(f'*{ext}'):
            if 'test' in path.relative_to(root_dir).parts:
                continue  # Skip test subdirectories.
            rpath = str(path.relative_to(root_dir))
            module_name = rpath[:-len(ext)].replace('/', '.')
            module = htypes.python_module.python_module(
                module_name=module_name,
                source=path.read_text(),
                file_path=str(path),
                )
            log.info("Fixture %s: %s", module_name, path)
            resource_module.set_definition(module_name, resource_type, module)
            


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        resource_module = services.resource_module_factory('fixtures')
        resource_type = services.resource_type_factory('python_module', htypes.python_module.python_module)
        load_fixtures(resource_module, resource_type, services.module_dir_list)
        services.resource_module_registry['fixtures'] = resource_module
