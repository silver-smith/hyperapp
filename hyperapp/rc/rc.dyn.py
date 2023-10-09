import logging
from dataclasses import dataclass, field

from hyperapp.common.htypes import HException

from .services import (
    hyperapp_dir,
    )
# from .code.make import Make
from .code.source_collector_task import SourceCollectorTask
from .code.process_pool import subprocess

log = logging.getLogger(__name__)


@dataclass
class Graph:
    name_to_unit: dict = field(default_factory=dict)
    name_to_deps: dict = field(default_factory=dict)
    dep_to_provider: dict = field(default_factory=dict)


def compile_resources(generator_ref, subdir_list, root_dirs, module_list, rpc_timeout):
    log.info("Compile resources at: %s, %s: %s", subdir_list, root_dirs, module_list)

    if subdir_list:
        dir_list = [hyperapp_dir / d for d in subdir_list]
    else:
        dir_list = [hyperapp_dir]

    graph = Graph({}, {}, {})
    # make = Make()
    initial_task = SourceCollectorTask(generator_ref, hyperapp_dir, dir_list)
    # make.run(initial_task)
    initial_task.run(graph)
    with subprocess('rc-driver', rpc_timeout) as process:
        task_list = []
        for unit in graph.name_to_unit.values():
            if unit.is_up_to_date(graph):
                continue
            task_list += unit.make_tasks()
        for task in task_list:
            log.info("Submit: %s", task)
            future = task.start(process, graph)
            try:
                result = future.result()
                log.info("%s result: %r", task, result)
                task.process_result(graph, result)
            except HException as x:
                log.info("%s error: %r", task, x)
                task.process_error(graph, x)
