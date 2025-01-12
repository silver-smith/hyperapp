import logging
import sys

from hyperapp.boot.init_logging import init_logging
from hyperapp.boot import cdr_coders  # register codec
from hyperapp.boot.services import HYPERAPP_DIR, Services

log = logging.getLogger('rc.main')


module_dir_list = [
    HYPERAPP_DIR,
    HYPERAPP_DIR / 'common',
    HYPERAPP_DIR / 'resource',
    HYPERAPP_DIR / 'system',
    HYPERAPP_DIR / 'transport',
    HYPERAPP_DIR / 'rpc',
    HYPERAPP_DIR / 'subprocess',
    HYPERAPP_DIR / 'rc',
    HYPERAPP_DIR / 'command_line',
    HYPERAPP_DIR / 'sample',
    HYPERAPP_DIR / 'ui',
    HYPERAPP_DIR / 'views',
    HYPERAPP_DIR / 'models',
    ]


# Standard atexit module fires it's callbacks _after_ thread shutdown is hanged
# because of system still running. Hack into ipython instead.
def ipython_atexit(fn):
    ip = get_ipython()
    original_restore_term_title = ip.restore_term_title
    def new_restore_term_title():
        fn()
        original_restore_term_title()
    ip.restore_term_title = new_restore_term_title


def setup_system():

    init_logging('ipython')

    services = Services(module_dir_list)
    services.init_services()
    ipython_atexit(services.stop)
    log.debug("Initialized.")

    resource_dir_list = services.resource_dir_list
    resource_registry = services.resource_registry
    resource_list_loader = services.resource_list_loader
    legacy_type_resource_loader = services.legacy_type_resource_loader
    local_types = services.local_types
    pyobj_creg = services.pyobj_creg

    resource_list_loader(resource_dir_list, resource_registry)
    resource_registry.update_modules(legacy_type_resource_loader(local_types))
    config = resource_registry['rc.config', 'config']
    module_res = resource_registry['system.system', 'system.module']
    module = pyobj_creg.animate(module_res)

    system = module.System()
    ipython_atexit(system.close)
    system.load_config(config)

    for service_name in system.service_names:
        service = system.resolve_service(service_name)
        globals()[service_name] = service

setup_system()
print("System is inited.")
