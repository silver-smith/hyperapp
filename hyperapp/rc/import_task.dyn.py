import logging

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code import import_driver, call_driver

log = logging.getLogger(__name__)


class TaskBase:

    def __init__(self, unit):
        self._unit = unit

    def __repr__(self):
        return f"<{self}>"

    def process_error(self, graph, exception):
        log.error("Error returned from driver: %s", exception.message)
        for line_list in exception.traceback:
            for line in line_list.rstrip().splitlines():
                log.error("\t%s", line)
        raise exception


class ImportTask(TaskBase):

    def __init__(self, unit, recorders, module_res):
        super().__init__(unit)
        self._recorders = recorders
        self._module_res = module_res

    def __str__(self):
        return f"{self.__class__.__name__}({self._unit.name})"

    def start(self, process):
        log.debug("Import: %s", self._unit.name)
        future = process.rpc_submit(import_driver.import_module)(
            import_recorders=self._recorders,
            module_ref=mosaic.put(self._module_res),
            )
        return future

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


class AttrEnumTask(ImportTask):
    pass


class AttrCallTask(TaskBase):

    def __init__(self, unit, attr_name, recorders, call_res):
        super().__init__(unit)
        self._attr_name = attr_name
        self._recorders = recorders
        self._call_res = call_res

    def __str__(self):
        return f"AttrCallTask({self._unit.name}:{self._attr_name})"

    def start(self, process):
        future = process.rpc_submit(call_driver.call_function)(
            import_recorders=self._recorders,
            call_result_ref=mosaic.put(self._call_res),
            trace_modules=[],
            )
        return future

    def process_result(self, graph, result):
        log.info("%s type: %s", self, web.summon(result.t))
        self._unit.add_imports(graph, set(result.imports))
        self._unit.set_attr_called()
