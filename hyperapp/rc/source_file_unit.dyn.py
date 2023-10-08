import logging
from collections import namedtuple
from functools import cached_property

from .services import (
    resource_module_factory,
    )

log = logging.getLogger(__name__)


ModuleInfo = namedtuple('ModuleInfo', 'use_modules want_services want_code test_services test_code provide_services')
ServiceDep = namedtuple('ServiceDep', 'service_name')


def _resource_module_to_module_info(resource_module):
    use_modules = set()
    want_services = set()
    want_code = set()
    for module_name, var_name in resource_module.used_imports:
        use_modules.add(module_name)
        l = var_name.split('.')
        if len(l) == 2 and l[1] == 'service':
            want_services.add(l[0])
        if len(l) > 1 and l[-1] == 'module':
            want_code.add('.'.join(l[:-1]))
    return ModuleInfo(
        use_modules=use_modules,
        want_services=want_services,
        want_code=want_code,
        test_services=set(),
        test_code=set(),
        provide_services=resource_module.provided_services,
        )


class SourceFileUnit:

    def __init__(self, generator_ref, root_dir, path):
        self._generator_ref = generator_ref
        self._path = path
        self._stem = path.name[:-len('.dyn.py')]
        self.name = str(path.relative_to(root_dir).with_name(self._stem)).replace('/', '.')
        self._resources_path = path.with_name(self._stem + '.resources.yaml')
        self._resource_module = None
        self._module_info = None

    def __repr__(self):
        return f"<SourceFileUnit {self.name!r}>"

    @cached_property
    def is_fixtures(self):
        return 'fixtures' in self.name.split('.')

    def init(self, graph, ctx):
        if not self._resources_path.exists():
            log.info("%s: missing", self.name)
            return
        resource_module = resource_module_factory(ctx.resource_registry, self.name, self._resources_path)
        if not resource_module.is_auto_generated:
            self.resource_module = resource_module
            ctx.resource_registry.set_module(self.name, self.resource_module)
            log.info("%s: manually generated", self.name)
            return
        self._module_info = _resource_module_to_module_info(resource_module)
        log.info("%s: module present: %s", self.name, self._module_info)
        if not self.is_fixtures:
            for service_name in self._module_info.provide_services:
                dep = ServiceDep(service_name)
                try:
                    provider = graph.dep_to_provider[dep]
                except KeyError:
                    pass
                else:
                    raise RuntimeError(f"More than one module provide service {service_name!r}: {provider!r} and {self!r}")
                graph.dep_to_provider[dep] = self

    @property
    def is_up_to_date(self, ctx):
        if not resource_module.is_auto_generated:
            return True
