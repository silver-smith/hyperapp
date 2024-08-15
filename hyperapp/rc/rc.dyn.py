import logging
import subprocess

from hyperapp.common.htypes import HException

from . import htypes
from .services import (
    hyperapp_dir,
    web,
    )
from .code.reconstructors import register_reconstructors
from .code.rc_constants import JobStatus
from .code.build import load_build
from .code.target_set import TargetSet
from .code.init_targets import init_targets
from .code.rc_filter import Filter

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


def _collect_output(target_set, failures, options):

    def write(path, text):
        if options.write:
            rc_log.info("Write: %s", path)
            path.write_text(text)

    total = 0
    changed = 0
    for target in target_set:
        if not target.completed or not target.has_output or target in failures:
            continue
        resource_path, text = target.get_output()
        path = hyperapp_dir / resource_path
        if path.exists():
            p = subprocess.run(
                ['diff', '-u', str(path), '-'],
                input=text.encode(),
                stdout=subprocess.PIPE,
                )
            if p.returncode == 0:
                rc_log.info("%s: No diffs", target.name)
            else:
                diffs = p.stdout.decode()
                line_count = len(diffs.splitlines())
                if options.show_diffs:
                    rc_log.info("%s: Diff %d lines\n%s", target.name, line_count, diffs)
                else:
                    rc_log.info("%s: Diff %d lines", target.name, line_count)
                write(path, text)
                changed += 1
        else:
            if options.show_diffs:
                rc_log.info("%s: New file, %d lines\n%s", target.name, len(text.splitlines()), text)
            else:
                rc_log.info("%s: New file, %d lines", target.name, len(text.splitlines()))
            write(path, text)
            changed += 1
        total += 1
    return (total, changed)


def _submit_jobs(pool, target_set, target_to_job, job_id_to_target, filter):
    for target in target_set.iter_ready():
        if target in target_to_job:
            continue
        if not filter.included(target):
            rc_log.debug("%s: not requested", target.name)
            continue
        try:
            job = target.make_job()
        except Exception as x:
            raise RuntimeError(f"For {target.name}: {x}") from x
        rc_log.debug("Submit %s (in queue: %d)", target.name, pool.queue_size)
        pool.submit(job)
        target_to_job[target] = job
        job_id_to_target[id(job)] = target


def _run(rc_job_result_creg, pool, target_set, filter, options):
    rc_log.info("%d targets", target_set.count)
    target_to_job = {}  # Jobs are never removed.
    job_id_to_target = {}
    failures = {}
    incomplete = {}
    should_run = True
    while should_run:
        _submit_jobs(pool, target_set, target_to_job, job_id_to_target, filter)
        if pool.job_count == 0:
            rc_log.info("Not all targets are completed, but there are no jobs")
            break
        prev_completed = set(target_set.iter_completed())
        for job, result_piece in pool.iter_completed(options.timeout):
            result = rc_job_result_creg.animate(result_piece)
            target = job_id_to_target[id(job)]
            rc_log.info("%s: %s", target.name, result.status.name)
            if result.status == JobStatus.failed:
                failures[target] = result
                if options.fail_fast:
                    should_run = False
                    break
            else:
                target.handle_job_result(target_set, result)
            if result.status == JobStatus.incomplete:
                incomplete[target] = result
        _update_completed(target_set, prev_completed)
        filter.update_deps()
        if target_set.all_completed:
            rc_log.info("All targets are completed")
            break
    if failures:
        rc_log.info("%d failures:\n", len(failures))
        for target in failures:
            rc_log.info("Failed: %s", target.name)
        rc_log.info("\n")
        for target, result in failures.items():
            rc_log.info("\n========== %s ==========\n%s%s\n", target.name, "".join(result.traceback), result.error)
    if incomplete and options.show_incomplete_traces:
        rc_log.info("%d incomplete:\n", len(incomplete))
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
    with_output, changed_count = _collect_output(target_set, failures, options)
    job_count = len(job_id_to_target)
    completed_count = len(list(target_set.iter_completed()))
    rc_log.info(
        "Total: %d, completed: %d; not completed: %d, jobs: %d, succeeded: %d; failed: %d; incomplete: %d, output: %d, changed: %d",
        target_set.count,
        completed_count,
        target_set.count - completed_count,
        job_count,
        (job_count - len(failures)),
        len(failures),
        len(incomplete),
        with_output,
        changed_count,
        )


def _main(cfg_item_creg, ctr_from_template_creg, rc_job_result_creg, system_config, pool, targets, options):
    build = load_build(hyperapp_dir)
    log.info("Loaded build:")
    build.report()

    target_set = TargetSet(hyperapp_dir, build.python_modules)
    init_targets(cfg_item_creg, ctr_from_template_creg, system_config, hyperapp_dir, target_set, build.python_modules, build.types)
    filter = Filter(target_set, targets)
    try:
        _run(rc_job_result_creg, pool, target_set, filter, options)
    except HException as x:
        if isinstance(x, htypes.rpc.server_error):
            log.error("Server error: %s", x.message)
            for entry in x.traceback:
                for line in entry.splitlines():
                    log.error("%s", line)


def compile_resources(system_config, cfg_item_creg, process_pool_running, rc_job_result_creg, ctr_from_template_creg, targets, process_count, options):
    rc_log.info("Compile resources: %s", ", ".join(targets) if targets else 'all')

    if options.verbose:
        rc_log.setLevel(logging.DEBUG)

    register_reconstructors()

    with process_pool_running(process_count, options.timeout) as pool:
        _main(cfg_item_creg, ctr_from_template_creg, rc_job_result_creg, system_config, pool, targets, options)
