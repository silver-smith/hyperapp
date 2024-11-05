import logging
import traceback
from collections import defaultdict
from itertools import groupby

from hyperapp.common.htypes import HException
from hyperapp.common.config_item_missing import ConfigItemMissingError
from hyperapp.resource.python_module import PythonModuleResourceImportError

from .services import (
    mosaic,
    )
from .code.config_ctl import (
    item_pieces_to_data,
    service_pieces_to_config,
    merge_system_config_pieces,
    )
from .code.import_recorder import IncompleteImportedObjectError
from .code.system import UnknownServiceError
from .code.actor_req import ActorReq
from .code.service_req import ServiceReq
from .code.service_ctr import ServiceTemplateCtr
from .code.system_probe import SystemProbe

log = logging.getLogger(__name__)


class SystemJob:

    def __init__(self, system_config_piece):
        self._system_config_piece = system_config_piece  # Used only from 'run' method, inside job process.

    def _resource_group(self, resource):
        if resource.is_system_resource:
            return 0
        if resource.is_service_resource:
            return 1
        return 2

    def _compose_resources_config(self, system, resource_list):
        service_to_items = defaultdict(list)
        for resource in resource_list:
            for service_name, item_list in resource.system_config_items.items():
                service_to_items[service_name] += item_list
        # We expect that later resource items will override former ones.
        for resource in resource_list:
            for service_name, item_list in resource.system_config_items_override.items():
                service_to_items[service_name] += item_list
        service_to_config_piece = {
            service_name: item_pieces_to_data(item_list)
            for service_name, item_list in service_to_items.items()
            }
        return service_pieces_to_config(service_to_config_piece)

    def _configure_system(self, system, resource_list):
        sorted_resource_list = sorted(resource_list, key=self._resource_group)
        for resource in sorted_resource_list:
            resource.configure_system(system)

    def _prepare_system(self, resources):
        system = SystemProbe()
        resources_config = self._compose_resources_config(system, resources)
        config = merge_system_config_pieces(self._system_config_piece, resources_config)
        system.load_config(config)
        self._configure_system(system, resources)
        system.migrate_globals()
        _ = system.resolve_service('marker_registry')  # Init markers.
        return system

    def _enum_constructor_refs(self, ctr_collector):
        for ctr in ctr_collector.constructors:
            yield mosaic.put(ctr.piece)

    def _prepare_traceback(self, x):
        traceback_entries = []
        cause = x
        while cause:
            traceback_entries += traceback.extract_tb(cause.__traceback__)
            last_cause = cause
            cause = cause.__cause__
        for idx, entry in enumerate(traceback_entries):
            if entry.name == 'exec_module':
                del traceback_entries[:idx + 1]
                break
        for idx, entry in enumerate(traceback_entries):
            fpath = entry.filename.split('/')[-2:]
            fname = '/'.join(fpath).replace('.dyn.py', '')
            if fname not in {'rc/test_job', 'system/system', 'rc/system_probe', 'rc/fixture_probe'}:
                del traceback_entries[:idx]
                break
        line_list = traceback.format_list(traceback_entries)
        if isinstance(last_cause, htypes.rpc.server_error):
            for entry in last_cause.traceback:
                line_list += [line + '\n' for line in entry.splitlines()]
        return line_list

    def _raise_error(self, x):
        traceback_lines = self._prepare_traceback(x)
        if isinstance(x, htypes.rpc.server_error):
            message = x.message
        else:
            message = str(x)
        error_msg = f"{type(x).__name__}: {message}"
        if isinstance(x, IncompleteImportedObjectError):
            self.incomplete_error(error_msg, traceback_lines[:-1])
        else:
            self.failed_error(error_msg, traceback_lines)

    def _raise_import_error(self, x):
        self._raise_error(x.original_error)

    def convert_errors(self, fn, *args, **kw):
        try:
            return fn(*args, **kw)
        except HException as x:
            error_msg = f"{type(x).__name__}: {x}"
            if isinstance(x, htypes.rc_job.unknown_service_error):
                req = ServiceReq(x.service_name)
                self.incomplete_error(error_msg, missing_reqs={req})
            if isinstance(x, htypes.rc_job.config_item_missing_error):
                key = pyobj_creg.invite(x.t)
                req = ActorReq(x.service_name, key)
                self.incomplete_error(error_msg, missing_reqs={req})
            raise
        except PythonModuleResourceImportError as x:
            self._raise_import_error(x)
        except UnknownServiceError as x:
            req = ServiceReq(x.service_name)
            error_msg = f"{type(x).__name__}: {x}"
            self.incomplete_error(error_msg, missing_reqs={req})
        except ConfigItemMissingError as x:
            req = ActorReq(x.service_name, x.key)
            error_msg = f"{type(x).__name__}: {x}"
            self.incomplete_error(error_msg, missing_reqs={req})
        except IncompleteImportedObjectError as x:
            if list(x.path[:1]) == ['htypes']:
                path = '.'.join(x.path)
                error_msg = f"Unknown type: {path}" 
                traceback = self._prepare_traceback(x)[:-1]
                self.failed_error(error_msg, traceback)
            else:
                self._raise_error(x)
        except BaseException as x:
            self._raise_error(x)
