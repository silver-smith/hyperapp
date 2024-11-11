import argparse
import logging
import subprocess
from collections import namedtuple
from pathlib import Path

from hyperapp.common.htypes import HException

from . import htypes
from .services import (
    hyperapp_dir,
    web,
    )
from .code.reconstructors import register_reconstructors
from .code.rc_constants import JobStatus
from .code.build import load_build
from .code.job_cache import JobCache
from .code.target_set import TargetSet
from .code.init_targets import init_targets
from .code.rc_filter import Filter

log = logging.getLogger(__name__)
rc_log = logging.getLogger('rc')


JOB_CACHE_PATH = Path.home() / '.local/share/hyperapp/rc-job-cache.cdr'


Options = namedtuple('Options', 'clean timeout verbose fail_fast write show_diffs show_incomplete_traces')
RcArgs = namedtuple('RcArgs', 'targets process_count options')


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


def _submit_jobs(rc_job_result_creg, options, pool, target_set, target_to_job, job_id_to_target, filter):
    for target in target_set.iter_ready():
        if target in target_to_job:
            continue  # Already submitted.
        if not filter.included(target):
            rc_log.debug("%s: not requested", target.name)
            continue
        try:
            job = target.make_job()
        except Exception as x:
            raise RuntimeError(f"For {target.name}: {x}") from x
        target_to_job[target] = job
        job_id_to_target[id(job)] = target
        rc_log.debug("Submit %s (in queue: %d)", target.name, pool.queue_size)
        pool.submit(job)


def _run(rc_job_result_creg, pool, job_cache, target_set, filter, options):
    rc_log.info("%d targets", target_set.count)
    target_to_job = {}  # Jobs are never removed.
    job_id_to_target = {}
    failures = {}
    incomplete = {}
    cached_count = 0
    should_run = True

    def _handle_result(job, result_piece):
        target = job_id_to_target[id(job)]
        result = rc_job_result_creg.animate(result_piece)
        # job_cache.put(target, job, result_piece)
        rc_log.info("%s: %s", target.name, result.desc)
        if result.status == JobStatus.failed:
            failures[target] = result
            if options.fail_fast:
                should_run = False
        else:
            target.handle_job_result(target_set, result)
        if result.status == JobStatus.incomplete:
            incomplete[target] = result
        if result.should_cache:
            job_cache.put(target_set.factory, target, target.src, result.used_reqs, result)

    while should_run:
        _submit_jobs(rc_job_result_creg, options, pool, target_set, target_to_job, job_id_to_target, filter)
        if pool.job_count == 0:
            rc_log.info("Not all targets are completed, but there are no jobs\n")
            break
        prev_completed = set(target_set.iter_completed())
        for job, result_piece in pool.iter_completed(options.timeout):
            _handle_result(job, result_piece)
            if not should_run:
                break
        _update_completed(target_set, prev_completed)
        filter.update_deps()
        if target_set.all_completed:
            rc_log.info("All targets are completed\n")
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
        if options.verbose or not target.completed and target not in failures:
            rc_log.info(
                "%s: %s, missing: %s, wants: %s",
                "Failed" if target in failures else "Completed" if target.completed else "Not completed",
                target.name,
                ", ".join(dep.name for dep in target.deps if not dep.completed),
                ", ".join(dep.name for dep in target.deps),
                )
    rc_log.info("Diffs:\n")
    with_output, changed_count = _collect_output(target_set, failures, options)
    job_count = len(job_id_to_target)
    completed_count = len(list(target_set.iter_completed()))
    rc_log.info(
        "Total: %d, completed: %d; not completed: %d, jobs: %d, cached: %d, succeeded: %d; failed: %d; incomplete: %d, output: %d, changed: %d",
        target_set.count,
        completed_count,
        target_set.count - completed_count,
        job_count,
        cached_count,
        (job_count - len(failures)),
        len(failures),
        len(incomplete),
        with_output,
        changed_count,
        )



def _parse_args(sys_argv):
    parser = argparse.ArgumentParser(description='Compile resources')
    parser.add_argument('--root-dir', type=Path, nargs='*', help="Additional resource root dirs")
    parser.add_argument('--clean', '-c', action='store_true', help="Clean build: do not use cached job results")
    parser.add_argument('--workers', type=int, default=1, help="Worker process count to start and use")
    parser.add_argument('--timeout', type=int, help="Base timeout for RPC calls and everything (seconds). Default is none")
    parser.add_argument('--write', '-w', action='store_true', help="Write changed resources")
    parser.add_argument('--show-diffs', '-d', action='store_true', help="Show diffs for constructed resources")
    parser.add_argument('--show-incomplete-traces', '-i', action='store_true', help="Show tracebacks for incomplete jobs")
    parser.add_argument('--fail-fast', '-x', action='store_true', help="Stop on first failure")
    parser.add_argument('--verbose', '-v', action='store_true', help="Verbose output")
    parser.add_argument('targets', type=str, nargs='*', help="Select only those targets to build")
    args = parser.parse_args(sys_argv)

    options = Options(
        clean=args.clean,
        timeout=args.timeout,
        verbose=args.verbose,
        fail_fast=args.fail_fast,
        write=args.write,
        show_diffs=args.show_diffs,
        show_incomplete_traces=args.show_incomplete_traces,
        )
    return RcArgs(
        targets=args.targets,
        process_count=args.workers,
        options=options,
    )


def compile_resources(system_config_template, config_ctl, ctr_from_template_creg, rc_job_result_creg, job_cache, pool, targets, options):
    job_cache = job_cache(JOB_CACHE_PATH, load=not options.clean)
    build = load_build(hyperapp_dir, job_cache)
    log.info("Loaded build:")
    build.report()

    target_set = TargetSet(hyperapp_dir, build.python_modules)
    init_targets(config_ctl, ctr_from_template_creg, system_config_template, hyperapp_dir, job_cache, target_set, build)
    filter = Filter(target_set, targets)
    try:
        _run(rc_job_result_creg, pool, build.job_cache, target_set, filter, options)
    except HException as x:
        if isinstance(x, htypes.rpc.server_error):
            log.error("Server error: %s", x.message)
            for entry in x.traceback:
                for line in entry.splitlines():
                    log.error("%s", line)
        else:
            raise
    finally:
        build.job_cache.save()


def rc_main(process_pool_running, compile_resources, sys_argv):
    args = _parse_args(sys_argv)
    rc_log.info("Compile resources: %s", ", ".join(args.targets) if args.targets else 'all')

    if args.options.verbose:
        rc_log.setLevel(logging.DEBUG)

    register_reconstructors()

    with process_pool_running(args.process_count, args.options.timeout) as pool:
        compile_resources(pool, args.targets, args.options)
