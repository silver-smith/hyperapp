import logging
from collections import namedtuple
from functools import cached_property
from operator import attrgetter

from hyperapp.common.htypes import ref_str

from . import htypes
from .services import (
    mosaic,
    resource_module_factory,
    web,
    )
from .code.dep import CodeDep, FixturesDep, ServiceDep
from .code.scaffolds import (
    discoverer_module_res,
    enum_dep_imports,
    function_call_res,
    invite_attr_constructors,
    recorder_module_res,
    test_call_res,
    types_import_list,
    )

log = logging.getLogger(__name__)


ResModuleInfo = namedtuple('DesModuleInfo', 'want_deps test_code test_services')
ImportsInfo = namedtuple('ImportsInfo', 'used_types want_deps test_code test_services')


def _recorder_piece_list(recorders):
    piece_list = []
    for module_name, recorder_list in recorders.items():
        for rec in recorder_list:
            import_recorder = htypes.inspect.import_recorder(module_name, rec)
            piece_list.append(import_recorder)
    return piece_list


def _module_import_list_to_dict(module_import_list):
    module_name_to_imports = defaultdict(set)
    for rec in module_import_list:
        module_name_to_imports[rec.module] |= set(rec.imports)
    return module_name_to_imports


def _resource_module_info(resource_module, code_module_name):
    want_deps = set()
    for module_name, var_name in resource_module.used_imports:
        l = var_name.split('.')
        if len(l) == 2 and l[1] == 'service':
            want_deps.add(ServiceDep(l[0]))
        if len(l) > 1 and l[-1] == 'module':
            code_name = '.'.join(l[:-1])
            want_deps.add(CodeDep(code_name))
    test_code = set()
    test_services = set()
    import_list = resource_module.code_module_imports(code_module_name)
    for name in import_list:
        l = name.split('.')
        if len(l) != 3:
            continue
        do, what, name = l
        if do != 'tested':
            continue
        if what == 'code':
            test_code.add(name)
        if what == 'services':
            test_services.add(name)
    return ResModuleInfo(
        want_deps=want_deps,
        test_code=test_code,
        test_services=test_services,
        )


def _enum_provided_services(attr_list):
    for attr in attr_list:
        for ctr_ref in attr.constructors:
            ctr = web.summon(ctr_ref)
            if isinstance(ctr, htypes.attr_constructors.service):
                yield ctr.name


def _imports_info(imports):
    used_types = set()
    want_deps = set()
    test_code = set()
    test_services = set()
    for imp in imports:
        if imp[-1] == 'shape':
            imp = imp[:-1]  # Revert pycharm debugger mangle.
        if len(imp) < 2:
            continue
        kind, name, *_ = imp
        if kind == 'htypes':
            if len(imp) < 3:
                continue
            _, type_module, type_name, *_ = imp
            used_types.add((type_module, type_name))
            continue
        if kind == 'services':
            want_deps.add(ServiceDep(name))
            continue
        if kind == 'code':
            want_deps.add(CodeDep(name))
            continue
        if kind == 'tested':
            if len(imp) < 3:
                continue
            _, kind, name, *_ = imp
            if kind == 'services':
                test_services.add(name)
                continue
            if kind == 'code':
                test_code.add(name)
                continue
        raise RuntimeError(f"Unknown import kind %r: %s", kind, '.'.join(imp))
    log.info("Discovered import deps: %s", want_deps)
    log.info("Discovered test_services: %s", test_services)
    log.info("Discovered test_code: %s", test_code)

    return ImportsInfo(
        used_types=used_types,
        want_deps=want_deps,
        test_code=test_code,
        test_services=test_services,
        )


class Unit:

    def __init__(self, graph, ctx, generator_ref, root_dir, path):
        self._graph = graph
        self._ctx = ctx
        self._generator_ref = generator_ref
        self._source_path = path
        self._stem = path.name[:-len('.dyn.py')]
        self.code_name = self._stem
        rel_dir = path.parent.relative_to(root_dir)
        self._dir = str(rel_dir).replace('/', '.')
        self.name = f'{self._dir}.{self._stem}'
        self._resources_path = path.with_name(self._stem + '.resources.yaml')
        self._resource_checked = False
        self._resource_module = None
        self._providers_are_set = False
        self._import_set = None
        self._attr_list = None  # inspect.attr|fn_attr|generator_fn_attr list
        self._attr_call_tasks = None  # task list
        self._attr_call_in_progress = None  # str set
        self._tests = set()  # TestsUnit set

    def __repr__(self):
        return f"<Unit {self.name!r}>"

    @property
    def is_builtins(self):
        return False

    @cached_property
    def is_fixtures(self):
        return False

    @cached_property
    def is_tests(self):
        return False

    @property
    def is_up_to_date(self):
        return False

    @property
    def is_imports_discovered(self):
        return self._import_set is not None

    def report_deps(self):
        pass

    async def run(self, process_pool):
        log.info("Run: %s", self)
        recorders, module_res = discoverer_module_res(self._ctx, self)
        await process_pool.run(
            import_driver.import_module,
            import_recorders=_recorder_piece_list(recorders),
            module_ref=mosaic.put(module_res),
            )


class FixturesDepsProviderUnit(Unit):

    def __init__(self, graph, ctx, generator_ref, root_dir, path):
        super().__init__(graph, ctx, generator_ref, root_dir, path)


class FixturesUnit(FixturesDepsProviderUnit):

    def __repr__(self):
        return f"<FixturesUnit {self.name!r}>"

    @cached_property
    def is_fixtures(self):
        return True


class TestsUnit(FixturesDepsProviderUnit):

    def __init__(self, graph, ctx, generator_ref, root_dir, path):
        super().__init__(graph, ctx, generator_ref, root_dir, path)

    def __repr__(self):
        return f"<TestsUnit {self.name!r}>"

    @cached_property
    def is_tests(self):
        return True
