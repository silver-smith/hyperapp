import logging

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code import driver

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
        raise exception


class ImportTask(TaskBase):

    def __str__(self):
        return f"ImportTask({self._unit.name})"

    def start(self, process):
        recorders, module_res = _discoverer_module_res(self._ctx, self._unit)
        log.debug("Import: %s", self._unit.name)
        future = process.rpc_submit(driver.import_module)(
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
        assert 0, self
