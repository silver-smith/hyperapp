import logging
from collections import namedtuple
from functools import cached_property
from operator import attrgetter

from hyperapp.common.htypes import ref_str

from . import htypes
from .services import (
    mosaic,
    resource_module_factory,
    )
from .code.dep import ServiceDep, CodeDep
from .code.import_task import ImportTask

log = logging.getLogger(__name__)


def _enum_resource_module_deps(resource_module):
    for module_name, var_name in resource_module.used_imports:
        l = var_name.split('.')
        if len(l) == 2 and l[1] == 'service':
            yield ServiceDep(l[0])
        if len(l) > 1 and l[-1] == 'module':
            code_name = '.'.join(l[:-1])
            yield CodeDep(code_name)


class SourceFileUnit:

    def __init__(self, ctx, generator_ref, root_dir, path):
        self._ctx = ctx
        self._generator_ref = generator_ref
        self._source_path = path
        self._stem = path.name[:-len('.dyn.py')]
        self.name = str(path.relative_to(root_dir).with_name(self._stem)).replace('/', '.')
        self._resources_path = path.with_name(self._stem + '.resources.yaml')
        self._current_source_ref_str = None
        self._resource_module = None
        self._module_info = None

    def __repr__(self):
        return f"<SourceFileUnit {self.name!r}>"

    @cached_property
    def is_fixtures(self):
        return 'fixtures' in self._stem.split('.')

    @cached_property
    def is_tests(self):
        return self._stem.split('.')[-1] == 'tests'

    def _set_providers(self, graph, provide_services):
        if self.is_fixtures or self.is_tests:
            return
        for service_name in provide_services:
            dep = ServiceDep(service_name)
            try:
                provider = graph.dep_to_provider[dep]
            except KeyError:
                pass
            else:
                raise RuntimeError(f"More than one module provide service {service_name!r}: {provider!r} and {self!r}")
            graph.dep_to_provider[dep] = self

    def init(self, graph):
        graph.dep_to_provider[CodeDep(self._stem)] = self
        if not self._resources_path.exists():
            log.info("%s: missing", self.name)
            return
        resource_module = resource_module_factory(self._ctx.resource_registry, self.name, self._resources_path)
        if not resource_module.is_auto_generated:
            self._resource_module = resource_module
            self._ctx.resource_registry.set_module(self.name, resource_module)
            log.info("%s: manually generated", self.name)
            return
        self._current_source_ref_str = resource_module.source_ref_str
        deps = list(_enum_resource_module_deps(resource_module))
        if self._hash_matches(graph, deps):
            self._resource_module = resource_module
            self._ctx.resource_registry.set_module(self.name, resource_module)
            self._set_providers(graph, resource_module.provided_services)
            log.info("%s: Up-to-date, provides: %s", self.name, resource_module.provided_services)

    @property
    def deps(self):
        if self._module_info:
            return self._module_info.want_deps
        else:
            return set()

    def _make_source_ref(self, dep_units):
        deps = [
            u.source_dep_record for u in
            sorted([self, *dep_units], key=attrgetter('name'))
            ]
        return mosaic.put(htypes.rc.module_deps(deps))

    @cached_property
    def source_dep_record(self):
        source_ref = mosaic.put(self._source_path.read_bytes())
        return htypes.rc.source_dep(self.name, source_ref)

    def _hash_matches(self, graph, deps):
        if not self._current_source_ref_str:
            return False
        dep_units = []
        for dep in deps:
            try:
                module = graph.dep_to_provider[dep]
            except KeyError:
                log.debug("%s: dep %s is missing", self.name, dep)
                return False
            if not module.is_up_to_date(graph):
                log.debug("%s: dep %s module %s is outdated", self.name, dep, module)
                return False
            dep_units.append(module)
        source_ref = self._make_source_ref(dep_units)
        return ref_str(source_ref) == self._current_source_ref_str

    def is_up_to_date(self, graph):
        if self._resource_module:
            return True
        return self._hash_matches(graph, self.deps)

    def make_tasks(self):
        return [ImportTask(self._ctx, self)]

    def make_module_res(self, import_list):
        return htypes.builtin.python_module(
            module_name=self._stem,
            source=self._source_path.read_text(),
            file_path=str(self._source_path),
            import_list=tuple(import_list),
            )
