import logging
from dataclasses import dataclass, field

from .services import (
    hyperapp_dir,
    )
# from .code.make import Make
from .code.source_collector_task import SourceCollectorTask

_log = logging.getLogger(__name__)


@dataclass
class Graph:
    name_to_unit: dict = field(default_factory=dict)
    name_to_deps: dict = field(default_factory=dict)
    name_to_provides: dict = field(default_factory=dict)


subprocess_module_dir_list = [
    hyperapp_dir / 'common',
    hyperapp_dir / 'resource',
    hyperapp_dir / 'transport',
    hyperapp_dir / 'rpc',
    hyperapp_dir / 'subprocess',
    ]


def compile_resources(generator_ref, subdir_list, root_dirs, module_list, rpc_timeout=10):
    _log.info("Compile resources at: %s, %s: %s", subdir_list, root_dirs, module_list)

    if subdir_list:
        dir_list = [hyperapp_dir / d for d in subdir_list]
    else:
        dir_list = [hyperapp_dir]

    graph = Graph({}, {}, {})
    # make = Make()
    initial_task = SourceCollectorTask(generator_ref, hyperapp_dir, dir_list)
    # make.run(initial_task)
    initial_task.submit()
