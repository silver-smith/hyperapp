import argparse
import logging
import subprocess
from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path

from hyperapp.boot.htypes import HException
from hyperapp.boot.project import (
    config_project_name,
    load_boot_config,
    load_texts,
    separate_configs,
    )

from . import htypes
from .services import (
    hyperapp_dir,
    project_factory,
    )
from .code.reconstructors import register_reconstructors
from .code.rc_constants import JobStatus
from .code.job_cache import JobCache
from .code.target_set import FullTargetSet, GlobalTargets
from .code.init_targets import add_base_target_items, create_target_set
from .code.rc_filter import Filter

log = logging.getLogger(__name__)
rc_log = logging.getLogger('rc')


JOB_CACHE_PATH = Path.home() / '.local/share/hyperapp/rc-job-cache.cdr'


Options = namedtuple('Options', 'clean timeout verbose fail_fast write show_diffs show_incomplete_traces check')
RcArgs = namedtuple('RcArgs', 'projects targets process_count options')


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

    def run(self, full_target_set):
        total_count = sum(ts.count for name, ts in full_target_set)
        ts_count = ", ".join(f"{name}: {ts.count}" for name, ts in full_target_set)
        rc_log.info("%d targets: %s", total_count, ts_count)
        for name, target_set in full_target_set:
            if not self._run_target_set_jobs(name, full_target_set, target_set):
                break
        self._report_traces()
        all_completed = self._all_completed(full_target_set)
        if not all_completed:
            rc_log.info("\n")
        for name, target_set in full_target_set:
            self._report_deps(name, target_set)
        rc_log.info("Diffs:\n")
        name_to_output_stats = {}
        for name, target_set in full_target_set:
            with_output, changed_count = self._collect_output(all_completed, target_set)
            name_to_output_stats[name] = with_output, changed_count
        self._report_stats(full_target_set, name_to_output_stats)

    def _run_target_set_jobs(self, name, full_target_set, target_set):
        while True:
            self._submit_jobs(target_set)
            if target_set.all_completed:
                rc_log.info("%s: All targets are completed", name)
                return True
            if self._pool.job_count == 0:
                rc_log.info("%s: Not all targets are completed, but there are no jobs", name)
                return True
            for job, result_piece in self._pool.iter_completed(self._options.timeout):
                result = self._handle_result(target_set, job, result_piece)
                if result.status == JobStatus.failed and self._options.fail_fast:
                    return False
            full_target_set.update_statuses()
            if self._options.check:
                full_target_set.check_statuses()
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

    def _report_deps(self, name, target_set):
        for target in target_set:
            if self._options.verbose or not target.completed and target not in self._failures:
                rc_log.info(
                    "%s: %s:%s, missing: %s, wants: %s",
                    "Failed" if target in self._failures else "Completed" if target.completed else "Not completed",
                    name,
                    target.name,
                    ", ".join(dep.name for dep in target.deps if not dep.completed),
                    ", ".join(dep.name for dep in target.deps),
                    )

    def _all_completed(self, full_target_set):
        return all(
            target_set.completed_count == target_set.count
            for name, target_set in full_target_set
            )

    def _report_stats(self, full_target_set, name_to_output_stats):
        total_count = 0
        total_completed_count = 0
        total_with_output = 0
        total_changed_count = 0
        for name, target_set in full_target_set:
            completed_count = target_set.completed_count
            with_output, changed_count = name_to_output_stats[name]
            job_count = sum(1 for target in self._job_id_to_target.values() if target in target_set)
            self._report_target_set_stats(name, target_set.count, completed_count, job_count, with_output, changed_count)
            total_count += target_set.count
            total_completed_count += completed_count
            total_with_output += with_output
            total_changed_count += changed_count
        self._report_total_stats(total_count, total_completed_count, total_with_output, total_changed_count)

    def _report_target_set_stats(self, name, total_count, completed_count, job_count, with_output, changed_count):
        rc_log.info(
            "%s: %d, completed: %d; not completed: %d, jobs: %d, output: %d, changed: %d",
            name,
            total_count,
            completed_count,
            total_count - completed_count,
            job_count,
            with_output,
            changed_count,
            )

    def _report_total_stats(self, total_count, completed_count, with_output, changed_count):
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

    def _collect_output(self, all_completed, target_set):
        total = 0
        changed = 0
        for target in target_set:
            if not target.completed or not target.has_output or target in self._failures:
                continue
            resource_path, text = target.get_output()
            if str(resource_path) == 'rc/config.resources.yaml':
                # RC project targets are not loaded; Applied to system directly as layer config.
                continue
            path = hyperapp_dir / resource_path
            if path.exists():
                p = subprocess.run(
                    ['diff', '-u', str(path), '-'],
                    input=text.encode(),
                    stdout=subprocess.PIPE,
                    )
                if p.returncode == 0:
                    rc_log.debug("%s: No diffs", resource_path)
                else:
                    diffs = p.stdout.decode()
                    line_count = len(diffs.splitlines())
                    if self._options.show_diffs:
                        rc_log.info("%s: Diff %d lines\n%s", resource_path, line_count, diffs)
                    else:
                        rc_log.info("%s: Diff %d lines", resource_path, line_count)
                    if all_completed and not self._failures:
                        self._write(path, text)
                    changed += 1
            else:
                if self._options.show_diffs:
                    rc_log.info("%s: New file, %d lines\n%s", resource_path, len(text.splitlines()), text)
                else:
                    rc_log.info("%s: New file, %d lines", resource_path, len(text.splitlines()))
                self._write(path, text)
                changed += 1
            total += 1
        return (total, changed)


def _parse_args(sys_argv):
    parser = argparse.ArgumentParser(description='Compile resources')
    parser.add_argument('--root-dir', type=Path, nargs='*', help="Additional resource root dirs")
    parser.add_argument('--projects', '-p', nargs='*', help="Select projects to build. By default, build all")
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
        projects=args.projects,
        targets=args.targets,
        process_count=args.workers,
        options=options,
    )


def build_target_sets(
        base_config_templates, config_ctl, ctr_from_template_creg,
        rc_config, job_cache, cached_count, only_target_projects, base_project):

    boot_config = load_boot_config(hyperapp_dir / 'projects.yaml')
    name_to_target_rec = {
        name: rec
        for name, rec
        in boot_config.projects.items()
        if not only_target_projects or name in only_target_projects
        }

    global_targets = GlobalTargets()
    full_target_set = FullTargetSet(global_targets)
    name_to_target_project = {}
    name_to_target_set = {}
    for name, rec in name_to_target_rec.items():
        project_imports = {
            name_to_target_project[import_name]
            for import_name in rec.imports
            }
        target_set_imports = {
            name_to_target_set[import_name]
            for import_name in rec.imports
            }
        project_dir = hyperapp_dir / name
        path_to_text = load_texts(project_dir)
        log.info("Loaded project %r: %s files", name, len(path_to_text))
        target_project = project_factory(project_dir, name, imports=project_imports)
        target_project.load_types(path_to_text)
        target_set = create_target_set(
            config_ctl, ctr_from_template_creg, rc_config,
            project_dir, job_cache, cached_count, global_targets, target_project, path_to_text, target_set_imports)
        if name == 'base':
            add_base_target_items(config_ctl, ctr_from_template_creg, base_config_templates, target_set, base_project)
        name_to_target_project[name] = target_project
        name_to_target_set[name] = target_set
        full_target_set.add_target_set(name, target_set)
    full_target_set.post_init()
    return full_target_set


def _load_base_configs(get_layer_config_templates, base_project):
    config_templates = {}
    path_to_text = load_texts(base_project.path)
    _, config_path_to_text = separate_configs(path_to_text)
    for path, text in config_path_to_text.items():
        config_name = config_project_name(path)
        project_name = f'{base_project.name}.{config_name}'
        config = get_layer_config_templates(project_name)
        config_templates.update(config)
    return config_templates


def compile_resources(
        system, get_layer_config_templates, config_ctl, ctr_from_template_creg, rc_job_result_creg,
        job_cache, name_to_project, pool, only_target_projects, targets, options):

    base_project = name_to_project['base']
    rc_config = system.config_to_data({
        **get_layer_config_templates('rc'),
        **_load_base_configs(get_layer_config_templates, base_project),
        })
    base_config_templates = get_layer_config_templates('base')

    job_cache = job_cache(JOB_CACHE_PATH, load=not options.clean)
    cached_count = Counter()

    full_target_set = build_target_sets(
        base_config_templates, config_ctl, ctr_from_template_creg,
        rc_config, job_cache, cached_count, only_target_projects, base_project)
    if options.check:
        full_target_set.check_statuses()

    filter = Filter(full_target_set, targets)
    runner = RcRunner(rc_job_result_creg, options, filter, pool, job_cache, cached_count)
    try:
        runner.run(full_target_set)
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
        compile_resources(name_to_project, pool, args.projects, args.targets, args.options)
