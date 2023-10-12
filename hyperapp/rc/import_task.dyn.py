import logging

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code import import_driver, call_driver

log = logging.getLogger(__name__)


# Module resource with import discoverer.
def _discoverer_module_res(ctx, unit):
    resource_list = [*ctx.type_recorder_res_list]

    resource_list += [
        htypes.import_recorder.resource(('services', 'mark'), mosaic.put(
            ctx.resource_registry['common.mark', 'mark.service'])),
        htypes.import_recorder.resource(('services', 'on_stop'), mosaic.put(
            ctx.resource_registry['builtins', 'on_stop.service'])),
        htypes.import_recorder.resource(('services', 'stop_signal'), mosaic.put(
            ctx.resource_registry['builtins', 'stop_signal.service'])),
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


def _enum_import_list(graph, dep_list, fixtures_unit):
    for dep in dep_list:
        if fixtures_unit and dep in fixtures_unit.provided_deps:
            provider = fixtures_unit
        else:
            provider = graph.dep_to_provider[dep]
        resource = provider.provided_dep_resource(dep)
        yield htypes.builtin.import_rec(dep.import_name, mosaic.put(resource))


def _recorder_module_res(graph, ctx, unit, fixtures_unit=None):
    resource_list = [*ctx.type_recorder_res_list]
    import_recorder_res = htypes.import_recorder.import_recorder(resource_list)
    import_recorder_ref = mosaic.put(import_recorder_res)
    recorders = [import_recorder_ref]

    deps = graph.name_to_deps[unit.name]
    dep_imports_it = _enum_import_list(graph, deps, fixtures_unit)

    module_res = unit.make_module_res([
        htypes.builtin.import_rec('htypes.*', import_recorder_ref),
        *dep_imports_it,
        ])
    return (recorders, module_res)


class TaskBase:

    def __init__(self, ctx, unit):
        self._ctx = ctx
        self._unit = unit

    def __repr__(self):
        return f"<{self}>"

    def process_result(self, graph, result):
        self._unit.set_imports(graph, set(result.imports))
        if result.error:
            error = web.summon(result.error)
            if not isinstance(error, htypes.import_discoverer.using_incomplete_object):
                raise error
            log.info("%s: Incomplete object: %s", self._unit.name, error.message)
        else:
            attr_list = [web.summon(ref) for ref in result.attr_list]
            self._unit.set_attributes(graph, attr_list)

    def process_error(self, graph, exception):
        log.error("Error returned from driver: %s", exception.message)
        for line_list in exception.traceback:
            for line in line_list.rstrip().splitlines():
                log.error("\t%s", line)
        raise exception


class ImportTask(TaskBase):

    def __str__(self):
        return f"ImportTask({self._unit.name})"

    def start(self, process):
        recorders, module_res = _discoverer_module_res(self._ctx, self._unit)
        log.debug("Import: %s", self._unit.name)
        future = process.rpc_submit(import_driver.import_module)(
            import_recorders=recorders,
            module_ref=mosaic.put(module_res),
            )
        return future


class AttrEnumTask(TaskBase):

    def __init__(self, ctx, unit, graph):
        self._ctx = ctx
        self._unit = unit
        self._graph = graph

    def __str__(self):
        return f"AttrEnumTask({self._unit.name})"

    def start(self, process):
        recorders, module_res = _recorder_module_res(self._graph, self._ctx, self._unit)
        log.debug("Enum attributes: %s", self._unit.name)
        future = process.rpc_submit(import_driver.import_module)(
            import_recorders=recorders,
            module_ref=mosaic.put(module_res),
            )
        return future


class AttrCallTask(TaskBase):

    def __init__(self, ctx, unit, graph, fixtures, attr_name):
        super().__init__(ctx, unit)
        self._graph = graph
        self._fixtures = fixtures
        self._attr_name = attr_name

    def __str__(self):
        return f"AttrCallTask({self._unit.name}:{self._attr_name})"

    def start(self, process):
        recorders, module_res = _recorder_module_res(self._graph, self._ctx, self._unit, self._fixtures)
        log.debug("Call attribute %s: %s", self._attr_name, self._unit.name)
        attr_res = htypes.builtin.attribute(
            object=mosaic.put(module_res),
            attr_name=self._attr_name,
            )
        future = process.rpc_submit(call_driver.call_function)(
            import_recorders=recorders,
            fn_ref=mosaic.put(attr_res),
            trace_modules=[],
            )
        return future

    def process_result(self, graph, result):
        self._unit.add_imports(graph, set(result.imports))
        self._unit.set_attr_called()
