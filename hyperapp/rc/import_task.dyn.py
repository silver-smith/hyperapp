import logging
from collections import namedtuple

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.dep import ServiceDep, CodeDep
from .code import driver

log = logging.getLogger(__name__)


DepsInfo = namedtuple('DepsInfo', 'want_deps test_services test_code')


# Module resource with import discoverer.
def _discoverer_module_res(ctx, unit):
    resource_list = [*ctx.type_recorder_res_list]

    resource_list += [
        htypes.import_recorder.resource(('services', 'mark'), mosaic.put(
            ctx.resource_registry['common.mark', 'mark.service'])),
        htypes.import_recorder.resource(('services', 'on_stop'), mosaic.put(
            ctx.resource_registry['builtin_service', 'on_stop'])),
        htypes.import_recorder.resource(('services', 'stop_signal'), mosaic.put(
            ctx.resource_registry['builtin_service', 'stop_signal'])),
        ]

    import_recorder_res = htypes.import_recorder.import_recorder(resource_list)
    import_recorder_ref = mosaic.put(import_recorder_res)
    import_discoverer_res = htypes.import_discoverer.import_discoverer()
    import_discoverer_ref = mosaic.put(import_discoverer_res)
    recorders = [import_recorder_ref, import_discoverer_ref]

    module_res = unit.make_module_res([
            htypes.builtin.import_rec('htypes.*', import_recorder_ref),
            htypes.builtin.import_rec('services.*', import_recorder_ref),
            htypes.builtin.import_rec('*', import_discoverer_ref),
            ])
    return (recorders, module_res)


def _imports_to_type_set(imports):
    used_types = set()
    for imp in imports:
        if len(imp) < 3:
            continue
        kind, module, name, *_ = imp
        if kind != 'htypes':
            continue
        used_types.add((module, name))
    return used_types


def _imports_to_deps(imports):
    want_deps = set()
    test_services = set()
    test_code = set()
    for imp in imports:
        if imp[-1] == 'shape':
            imp = imp[:-1]  # Revert pycharm debugger mangle.
        if len(imp) < 2:
            continue
        kind, name, *_ = imp
        if kind == 'htypes':
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

    return DepsInfo(
        want_deps=want_deps,
        test_services=test_services,
        test_code=test_code,
        )


class ImportTask:

    def __init__(self, ctx, module_unit):
        self._ctx = ctx
        self._unit = module_unit

    def __repr__(self):
        return f"<{self}>"

    def __str__(self):
        return f"ImportTask({self._unit.name})"

    def start(self, process, graph):
        recorders, module_res = _discoverer_module_res(self._ctx, self._unit)
        log.debug("Import: %s", self._unit.name)
        future = process.rpc_submit(driver.import_module)(
            import_recorders=recorders,
            module_ref=mosaic.put(module_res),
            )
        return future

    def process_result(self, graph, result):
        if result.error:
            error = web.summon(result.error)
            if not isinstance(error, htypes.import_discoverer.using_incomplete_object):
                raise error
            log.info("Incomplete object: %s", error.message)
        used_types = _imports_to_type_set(result.imports)
        deps = _imports_to_deps(result.imports)

    def process_error(self, graph, exception):
        raise exception
