import logging

from hyperapp.common.htypes import HException

from . import htypes
from .services import (
    hyperapp_dir,
    rc_job_result_creg,
    web,
    )
from .code.reconstructors import register_reconstructors
from .code.process_pool import process_pool_running
from .code.rc_constants import JobStatus
from .code.build import load_build
from .code.target_set import TargetSet
from .code.import_target import create_import_targets

log = logging.getLogger(__name__)
rc_log = logging.getLogger('rc')


def _update_completed(target_set, prev_completed):
    while True:
        completed = set(target_set.iter_completed())
        new_completed = completed - prev_completed
        if not new_completed:
            break
        for target in new_completed:
            target_set.update_deps_statuses(target)
        prev_completed = completed


def _run(pool, target_set, fail_fast, timeout):
    rc_log.info("%d targets", target_set.count)
    target_to_job = {}  # Jobs are never removed.
    job_id_to_target = {}
    job_count = 0
    failures = {}
    incomplete = {}
    should_run = True
    while should_run:
        for target in target_set.iter_ready():
            if target in target_to_job:
                continue
            job = target.make_job()
            rc_log.debug("Submit %s", target.name)
            pool.submit(job)
            target_to_job[target] = job
            job_id_to_target[id(job)] = target
        prev_completed = set(target_set.iter_completed())
        for job, result_piece in pool.iter_completed(timeout):
            result = rc_job_result_creg.animate(result_piece)
            target = job_id_to_target[id(job)]
            rc_log.info("%s: %s", target.name, result.status.name)
            job_count += 1
            if result.status == JobStatus.failed:
                failures[target] = result
                if fail_fast:
                    should_run = False
                    break
            else:
                target.handle_job_result(target_set, result)
            if result.status == JobStatus.incomplete:
                incomplete[target] = result
        _update_completed(target_set, prev_completed)
        if target_set.all_completed:
            rc_log.info("All targets are completed")
            break
        if pool.job_count == 0:
            rc_log.info("Not all targets are completed, but there are no jobs")
            break
    if failures:
        rc_log.info("Failures:\n")
        for target, result in failures.items():
            rc_log.info("\n========== %s ==========\n%s%s\n", target.name, "".join(result.traceback), result.error)
    if incomplete:
        rc_log.info("Incomplete:\n")
        for target, result in incomplete.items():
            rc_log.info("\n========== %s ==========\n%s%s\n", target.name, "".join(result.traceback), result.error)
    for target in target_set:
        if not target.completed and target not in failures:
            rc_log.info(
                "Not completed: %s, missing: %s, wants: %s",
                target.name,
                ", ".join(dep.name for dep in target.deps if not dep.completed),
                ", ".join(dep.name for dep in target.deps),
                )
    rc_log.info("Completed: %d; succeeded: %d; failed: %d; incomplete: %d", job_count, (job_count - len(failures)), len(failures), len(incomplete))


def _main(pool, fail_fast, timeout):
    build = load_build(hyperapp_dir)
    log.info("Loaded build:")
    build.report()

    target_set = TargetSet(build.python_modules)
    create_import_targets(hyperapp_dir, target_set, build.python_modules, build.types)
    try:
        _run(pool, target_set, fail_fast, timeout)
    except HException as x:
        if isinstance(x, htypes.rpc.server_error):
            log.error("Server error: %s", x.message)
            for entry in x.traceback:
                for line in entry.splitlines():
                    log.error("%s", line)


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
