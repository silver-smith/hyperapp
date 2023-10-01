import logging
from collections import namedtuple

from .services import (
    hyperapp_dir,
    )
# from .code.make import Make
from .code.source_collector_task import SourceCollectorTask

_log = logging.getLogger(__name__)


Graph = namedtuple('Graph', 'name_to_unit name_to_deps name_to_provides')


subprocess_module_dir_list = [
    hyperapp_dir / 'common',
    hyperapp_dir / 'resource',
    hyperapp_dir / 'transport',
    hyperapp_dir / 'rpc',
    hyperapp_dir / 'subprocess',
    ]


def compile_resources(generator_ref, subdir_list, root_dirs, module_list, rpc_timeout=10):
    _log.info("Compile resources at: %s, %s: %s", subdir_list, root_dirs, module_list)

    dir_list = [hyperapp_dir / d for d in subdir_list]
    graph = Graph({}, {}, {})
    # make = Make()
    initial_task = SourceCollectorTask(generator_ref, hyperapp_dir, dir_list)
    # make.run(initial_task)
    initial_task.submit()
