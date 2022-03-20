import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


def python_object(piece, python_object_creg):
    fn = python_object_creg.invite(piece.function)
    return fn()


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
                )
            log.info("Fixture: %s", module_name)
            resource_module.set_definition(module_name, resource_type, module)
            


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        resource_module = services.resource_module_factory('fixtures')
        resource_type = services.resource_type_factory('python_module', htypes.python_module.python_module)
        load_fixtures(resource_module, resource_type, services.module_dir_list)
        services.resource_module_registry['fixtures'] = resource_module
        # services.python_object_creg.register_actor(htypes.python_module.python_module, python_object, services.python_object_creg)
