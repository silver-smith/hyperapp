import logging

from .services import (
    hyperapp_dir,
    web,
    )
from .code.reconstructors import register_reconstructors
from .code.process_pool import process_pool_running
from .code.build import load_build
from .code.import_target import ImportTarget
from .code.rc_constants import JobStatus

log = logging.getLogger(__name__)
rc_log = logging.getLogger('rc')


def _setup_targets(build):
    for module in build.python_modules:
        yield ImportTarget(module, build.types)


def _run(pool, target_set, fail_fast, timeout):
    rc_log.info("%d targets", len(target_set))
    target_to_job = {}  # Jobs are never removed.
    job_id_to_target = {}
    job_count = 0
    failures = {}
    should_run = True
    while should_run:
        for target in target_set:
            if target in target_to_job:
                continue
            if target.ready:
                job = target.make_job()
                rc_log.debug("Submit %s", target.name)
                pool.submit(job)
                target_to_job[target] = job
                job_id_to_target[id(job)] = target
        for job, result_piece in pool.iter_completed(timeout):
            target = job_id_to_target[id(job)]
            result = target.handle_job_result(result_piece)
            rc_log.info("%s: %s", target.name, result.status.name)
            job_count += 1
            if result.status == JobStatus.failed:
                failures[target] = result
                if fail_fast:
                    should_run = False
                    break
        if all(t.completed for t in target_set):
            rc_log.info("All targets are completed")
            break
        if pool.job_count == 0:
            rc_log.info("Not all targets are completed, but there are no jobs")
            break
    rc_log.info("Failures:\n")
    for target, result in failures.items():
        rc_log.info("\n========== %s ==========\n%s%s\n", target.name, "".join(result.traceback), result.message)
    rc_log.info("Completed: %d; succeeded: %d; failed: %d", job_count, (job_count - len(failures)), len(failures))


def _main(pool, fail_fast, timeout):
    build = load_build(hyperapp_dir)
    log.info("Loaded build:")
    build.report()

    targets = {*_setup_targets(build)}
    _run(pool, targets, fail_fast, timeout)


def compile_resources(generator_ref, subdir_list, root_dirs, module_list, process_count, verbose, fail_fast, timeout):
    log.info("Compile resources at: %s, %s: %s", subdir_list, root_dirs, module_list)

    if verbose:
        rc_log.setLevel(logging.DEBUG)

    register_reconstructors()

    if subdir_list:
        dir_list = [hyperapp_dir / d for d in subdir_list]
    else:
        dir_list = [hyperapp_dir]

    with process_pool_running(process_count, timeout) as pool:
        _main(pool, fail_fast, timeout)
