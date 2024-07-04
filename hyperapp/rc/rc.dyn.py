import logging

from .services import (
    hyperapp_dir,
    web,
    )
from .code.reconstructors import register_reconstructors
from .code.process_pool import process_pool_running
from .code.build import load_build
from .code.import_target import ImportTarget

log = logging.getLogger(__name__)
rc_log = logging.getLogger('rc')


def _setup_targets(build):
    for module in build.python_modules:
        yield ImportTarget(module, build.types)


def _run(pool, target_set):
    target_to_job = {}  # Jobs are never removed.
    job_id_to_target = {}
    while True:
        for target in target_set:
            if target in target_to_job:
                continue
            if target.ready:
                job = target.job
                rc_log.info("Submit %s", target.name)
                pool.submit(job)
                target_to_job[target] = job
                job_id_to_target[id(job)] = target
        for job, result in pool.iter_completed():
            target = job_id_to_target[id(job)]
            rc_log.info("Finished %s: %r", target.name, result)
            target.set_job_result(result)
        if all(t.completed for t in target_set):
            rc_log.info("All targets are completed")
            break
        if pool.job_count == 0:
            rc_log.info("Not all targets are completed, but there are no jobs")
            break


def _main(pool, timeout):
    build = load_build(hyperapp_dir)
    log.info("Loaded build:")
    build.report()

    targets = {*_setup_targets(build)}
    _run(pool, targets)


def compile_resources(generator_ref, subdir_list, root_dirs, module_list, process_count, show_traces, timeout):
    rc_log.info("Compile resources at: %s, %s: %s", subdir_list, root_dirs, module_list)

    register_reconstructors()

    if subdir_list:
        dir_list = [hyperapp_dir / d for d in subdir_list]
    else:
        dir_list = [hyperapp_dir]

    with process_pool_running(process_count, timeout) as pool:
        _main(pool, timeout)
