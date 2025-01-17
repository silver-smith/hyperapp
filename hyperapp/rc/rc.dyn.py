import argparse
import logging
import subprocess
from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path

from hyperapp.boot.htypes import HException
from hyperapp.boot.project import load_texts

from . import htypes
from .services import (
    hyperapp_dir,
    web,
    )
from .code.reconstructors import register_reconstructors
from .code.rc_constants import JobStatus
from .code.job_cache import JobCache
from .code.init_targets import add_base_target_items, create_target_set
from .code.rc_filter import Filter

log = logging.getLogger(__name__)
rc_log = logging.getLogger('rc')


JOB_CACHE_PATH = Path.home() / '.local/share/hyperapp/rc-job-cache.cdr'


Options = namedtuple('Options', 'clean timeout verbose fail_fast write show_diffs show_incomplete_traces check')
RcArgs = namedtuple('RcArgs', 'targets process_count options')


@dataclass
class Counter:
    value: int = 0

    def incr(self):
        self.value += 1


class RcRunner:

    def __init__(self, rc_job_result_creg, options, filter, pool, job_cache, cached_count):
        self._rc_job_result_creg = rc_job_result_creg
        self._options = options
        self._filter = filter
        self._pool = pool
        self._job_cache = job_cache
        self._cached_count = cached_count
        self._target_to_job = {}  # Jobs are never removed.
        self._job_id_to_target = {}
        self._failures = {}
        self._incomplete = {}

    def _submit_jobs(self, target_set):
        for target in target_set.iter_ready():
            if target in self._target_to_job:
                continue  # Already submitted.
            if not self._filter.included(target):
                rc_log.debug("%s: not requested", target.name)
                continue
            try:
                job = target.make_job()
            except Exception as x:
                raise RuntimeError(f"For {target.name}: {x}") from x
            self._target_to_job[target] = job
            self._job_id_to_target[id(job)] = target
            rc_log.debug("Submit %s (in queue: %d)", target.name, self._pool.queue_size)
            self._pool.submit(job)

    def _handle_result(self, target_set, job, result_piece):
        target = self._job_id_to_target[id(job)]
        result = self._rc_job_result_creg.animate(result_piece)
        rc_log.info("%s: %s", target.name, result.desc)
        if result.status == JobStatus.failed:
            self._failures[target] = result
        else:
            target.handle_job_result(target_set, result)
        if result.status == JobStatus.incomplete:
            self._incomplete[target] = result
        cache_target_name = result.cache_target_name(target)
        if cache_target_name:
            req_to_resources = job.req_to_resources
            deps = {
                req: req_to_resources[req]
                for req in result.used_reqs
                }
            self._job_cache.put(cache_target_name, target.src, deps, result)
        return result

    def run(self, target_set):
        rc_log.info("%d targets", target_set.count)
        self._run_target_set_jobs(target_set)
        self._report_traces()
        self._report_deps(target_set)
        rc_log.info("Diffs:\n")
        with_output, changed_count = self._collect_output(target_set)
        completed_count = len(list(target_set.iter_completed()))
        self._report_stats(target_set.count, completed_count, with_output, changed_count)

    def _run_target_set_jobs(self, target_set):
        while True:
            self._submit_jobs(target_set)
            if target_set.all_completed:
                rc_log.info("All targets are completed\n")
                return
            if self._pool.job_count == 0:
                rc_log.info("Not all targets are completed, but there are no jobs\n")
                return
            for job, result_piece in self._pool.iter_completed(self._options.timeout):
                result = self._handle_result(target_set, job, result_piece)
                if result.status == JobStatus.failed and self._options.fail_fast:
                    return
            target_set.update_statuses()
            if self._options.check:
                target_set.check_statuses()
            self._filter.update_deps()

    def _report_traces(self):
        if self._failures:
            rc_log.info("%d failures:\n", len(self._failures))
            for target in self._failures:
                rc_log.info("Failed: %s", target.name)
            rc_log.info("\n")
            for target, result in self._failures.items():
                rc_log.info("\n========== %s ==========\n%s%s\n", target.name, "".join(result.traceback), result.error)
        if self._incomplete and self._options.show_incomplete_traces:
            rc_log.info("%d incomplete:\n", len(self._incomplete))
            for target, result in self._incomplete.items():
                rc_log.info("\n========== %s ==========\n%s%s\n", target.name, "".join(result.traceback), result.error)

    def _report_deps(self, target_set):
        for target in target_set:
            if self._options.verbose or not target.completed and target not in self._failures:
                rc_log.info(
                    "%s: %s, missing: %s, wants: %s",
                    "Failed" if target in self._failures else "Completed" if target.completed else "Not completed",
                    target.name,
                    ", ".join(dep.name for dep in target.deps if not dep.completed),
                    ", ".join(dep.name for dep in target.deps),
                    )

    def _report_stats(self, total_count, completed_count, with_output, changed_count):
        job_count = len(self._job_id_to_target)
        rc_log.info(
            "Total: %d, completed: %d; not completed: %d, jobs: %d, cached: %d, succeeded: %d; failed: %d; incomplete: %d, output: %d, changed: %d",
            total_count,
            completed_count,
            total_count - completed_count,
            job_count,
            self._cached_count.value,
            (job_count - len(self._failures)),
            len(self._failures),
            len(self._incomplete),
            with_output,
            changed_count,
            )

    def _write(self, path, text):
        if self._options.write:
            rc_log.info("Write: %s", path)
            path.write_text(text)

    def _collect_output(self, target_set):
        total = 0
        changed = 0
        for target in target_set:
            if not target.completed or not target.has_output or target in self._failures:
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
                    rc_log.debug("%s: No diffs", target.name)
                else:
                    diffs = p.stdout.decode()
                    line_count = len(diffs.splitlines())
                    if self._options.show_diffs:
                        rc_log.info("%s: Diff %d lines\n%s", target.name, line_count, diffs)
                    else:
                        rc_log.info("%s: Diff %d lines", target.name, line_count)
                    self._write(path, text)
                    changed += 1
            else:
                if self._options.show_diffs:
                    rc_log.info("%s: New file, %d lines\n%s", target.name, len(text.splitlines()), text)
                else:
                    rc_log.info("%s: New file, %d lines", target.name, len(text.splitlines()))
                self._write(path, text)
                changed += 1
            total += 1
        return (total, changed)


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
    parser.add_argument('--check', action='store_true', help="Perform internal checks")
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
        check=args.check,
        )
    return RcArgs(
        targets=args.targets,
        process_count=args.workers,
        options=options,
    )


def compile_resources(
        system_config_template, config_ctl, ctr_from_template_creg, rc_job_result_creg,
        job_cache, name_to_project, pool, targets, options):

    job_cache = job_cache(JOB_CACHE_PATH, load=not options.clean)
    cached_count = Counter()

    name_to_target_set = {}
    for name, project in name_to_project.items():
        imports = {
            name_to_target_set[p.name]
            for p in project.imports
            }
        path_to_text = load_texts(hyperapp_dir / project.name)
        log.info("Loaded project %r: %s files", name, len(path_to_text))
        target_set = create_target_set(
            config_ctl, ctr_from_template_creg, system_config_template, hyperapp_dir / name, job_cache, cached_count,
            name, path_to_text, imports)
        if name == 'base':
            add_base_target_items(config_ctl, ctr_from_template_creg, system_config_template, target_set, project)
        target_set.post_init()
        name_to_target_set[name] = target_set

    if options.check:
        target_set.check_statuses()
    filter = Filter(target_set, targets)
    runner = RcRunner(rc_job_result_creg, options, filter, pool, job_cache, cached_count)
    try:
        runner.run(name_to_target_set)
    except HException as x:
        if isinstance(x, htypes.rpc.server_error):
            log.error("Server error: %s", x.message)
            for entry in x.traceback:
                for line in entry.splitlines():
                    log.error("%s", line)
        else:
            raise
    finally:
        job_cache.save()


def rc_main(process_pool_running, compile_resources, name_to_project, sys_argv):
    args = _parse_args(sys_argv)
    rc_log.info("Compile resources: %s", ", ".join(args.targets) if args.targets else 'all')

    if args.options.verbose:
        rc_log.setLevel(logging.DEBUG)

    register_reconstructors()

    with process_pool_running(args.process_count, args.options.timeout) as pool:
        compile_resources(name_to_project, pool, args.targets, args.options)
