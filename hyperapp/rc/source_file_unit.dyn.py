import logging
from collections import namedtuple

from .services import (
    resource_module_factory,
    )

log = logging.getLogger(__name__)


DepsInfo = namedtuple('DepsInfo', 'uses_modules wants_services wants_code tests_services tests_code')


def _get_resource_module_deps(resource_module):
    uses_modules = set()
    wants_services = set()
    wants_code = set()
    for module_name, var_name in resource_module.used_imports:
        uses_modules.add(module_name)
        l = var_name.split('.')
        if len(l) == 2 and l[1] == 'service':
            wants_services.add(l[0])
        if len(l) > 1 and l[-1] == 'module':
            wants_code.add('.'.join(l[:-1]))
    return DepsInfo(
        uses_modules=uses_modules,
        wants_services=wants_services,
        wants_code=wants_code,
        tests_services=set(),
        tests_code=set(),
        )


class SourceFileUnit:

    def __init__(self, generator_ref, root_dir, path):
        self._generator_ref = generator_ref
        self._path = path
        self._stem = path.name[:-len('.dyn.py')]
        self.name = str(path.relative_to(root_dir).with_name(self._stem)).replace('/', '.')
        self._resources_path = path.with_name(self._stem + '.resources.yaml')
        self._resource_module = None

    def __repr__(self):
        return f"<SourceFileUnit {self.name!r}>"

    def init(self, ctx):
        if not self._resources_path.exists():
            log.info("%s: missing", self.name)
            return
        resource_module = resource_module_factory(ctx.resource_registry, self.name, self._resources_path)
        if not resource_module.is_auto_generated:
            self.resource_module = resource_module
            ctx.resource_registry.set_module(self.name, self.resource_module)
            log.info("%s: manually generated", self.name)
            return
        deps = _get_resource_module_deps(resource_module)

    @property
    def is_up_to_date(self):
        return False
