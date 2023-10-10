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


class ImportTask:

    def __init__(self, ctx, module_unit):
        self._ctx = ctx
        self._unit = module_unit

    def __repr__(self):
        return f"<{self}>"

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

    def process_result(self, graph, result):
        if result.error:
            error = web.summon(result.error)
            if not isinstance(error, htypes.import_discoverer.using_incomplete_object):
                raise error
            log.info("Incomplete object: %s", error.message)
        self._unit.set_imports(graph, set(result.imports))

    def process_error(self, graph, exception):
        raise exception
