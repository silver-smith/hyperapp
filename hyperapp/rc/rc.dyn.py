import logging

from .services import (
    hyperapp_dir,
    )
from .code.reconstructors import register_reconstructors
from .code.process_pool import process_pool_running
from .code.import_job import ImportJob

log = logging.getLogger(__name__)


def _main(pool, timeout):
    job = ImportJob()
    pool.submit(job)
    job, result = pool.next_completed(timeout=timeout)
    log.info("%s result: %r", job, result)


def compile_resources(generator_ref, subdir_list, root_dirs, module_list, process_count, show_traces, timeout):
    log.info("Compile resources at: %s, %s: %s", subdir_list, root_dirs, module_list)

    register_reconstructors()

    if subdir_list:
        dir_list = [hyperapp_dir / d for d in subdir_list]
    else:
        dir_list = [hyperapp_dir]

    with process_pool_running(process_count, timeout) as pool:
        _main(pool, timeout)
