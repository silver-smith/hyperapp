import logging
from collections import defaultdict

from hyperapp.common.htypes import HException

from .services import (
    hyperapp_dir,
    )
# from .code.make import Make
from .code.collector_task import CollectorTask
from .code.process_pool import process_pool_running

log = logging.getLogger(__name__)


class Graph:

    def __init__(self):
        self.name_to_unit = {}
        self.name_to_deps = defaultdict(set)
        self.dep_to_provider = {}


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


def compile_resources(generator_ref, subdir_list, root_dirs, module_list, process_count, rpc_timeout):
    log.info("Compile resources at: %s, %s: %s", subdir_list, root_dirs, module_list)

    if subdir_list:
        dir_list = [hyperapp_dir / d for d in subdir_list]
    else:
        dir_list = [hyperapp_dir]

    graph = Graph()
    # make = Make()
    initial_task = CollectorTask(generator_ref, hyperapp_dir, dir_list)
    try:
        # make.run(initial_task)
        initial_task.run(graph)
        with process_pool_running(process_count, rpc_timeout) as pool:
            task_to_unit = {}
            while True:
                for unit in graph.name_to_unit.values():
                    if unit in task_to_unit.values():
                        continue  # No finished tasks for this unit yet.
                    if unit.is_up_to_date:
                        continue
                    for task in unit.make_tasks():
                        log.info("Submit: %s", task)
                        pool.submit(task)
                        task_to_unit[task] = unit
                if not task_to_unit and pool.task_count == 0:
                    break
                task, future = pool.next_completed(timeout=rpc_timeout)
                del task_to_unit[task]
                try:
                    result = future.result()
                    log.info("%s result: %r", task, result)
                    task.process_result(graph, result)
                except HException as x:
                    log.info("%s error: %r", task, x)
                    task.process_error(graph, x)

        _report_not_compiled(graph)

    finally:
        _dump_graph(graph)

