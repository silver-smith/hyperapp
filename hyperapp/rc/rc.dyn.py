import asyncio
import logging
import traceback
from collections import defaultdict

from hyperapp.common.htypes import HException

from .services import (
    hyperapp_dir,
    )
from .code.collector import collect_units
from .code.process_pool import process_pool_running

log = logging.getLogger(__name__)


class Graph:

    def __init__(self):
        self.name_to_unit = {}
        self.dep_to_provider = {}
        self.name_to_deps = defaultdict(set)

    def unit_by_code_name(self, code_name):
        for unit in self.name_to_unit.values():
            if unit.code_name == code_name:
                return unit
        raise RuntimeError(f"Unknown code module: {code_name}")


def _report_not_compiled(graph):
    for unit in graph.name_to_unit.values():
        if unit.is_up_to_date:
            continue
        log.info("Not compiled: %s", unit.name)
        unit.report_deps()


def _dump_graph(graph):
    for name, deps in sorted(graph.name_to_deps.items()):
        log.debug("Deps for %s: %s", name, deps or '{}')
    for dep, provider in sorted(graph.dep_to_provider.items()):
        log.debug("Provider for %s: %s", dep, provider)



async def _run_unit(unit, process_pool, show_traces):
    if show_traces:
        error_logger = log.exception
    else:
        error_logger = log.info
    try:
        return await unit.run(process_pool)
    except asyncio.CancelledError as x:
        x.__context__ = None
        if any('process_available.wait' in s for s in traceback.format_exception(x)):
            error_logger("Waiting for a process: %s", unit)
        elif any('unit_constructed.wait' in s for s in traceback.format_exception(x)):
            error_logger("Waiting for a unit to be constructed: %s", unit)
        else:
            error_logger("Cancelled: %s", unit)
    except Exception as x:
        error_logger("Failed: %s: %s", unit, x)
        raise RuntimeError(f"{unit}: {x}")


async def _main(graph, process_pool, show_traces):
    unit_tasks = [_run_unit(unit, process_pool, show_traces) for unit in graph.name_to_unit.values()]
    try:
        await asyncio.gather(process_pool.check_for_deadlock(), *unit_tasks)
    except TimeoutError:
        log.error("Deadlocked\n")


def compile_resources(generator_ref, subdir_list, root_dirs, module_list, process_count, show_traces, rpc_timeout):
    log.info("Compile resources at: %s, %s: %s", subdir_list, root_dirs, module_list)

    if subdir_list:
        dir_list = [hyperapp_dir / d for d in subdir_list]
    else:
        dir_list = [hyperapp_dir]

    graph = Graph()
    try:
        collect_units(hyperapp_dir, dir_list, generator_ref, graph)
        with process_pool_running(process_count, rpc_timeout) as pool:
            asyncio.run(_main(graph, pool, show_traces))
        _report_not_compiled(graph)
    finally:
        _dump_graph(graph)
