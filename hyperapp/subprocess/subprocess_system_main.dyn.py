from .code.system import run_system


def system_main(connection, received_refs, system_config, root_name, **kw):
    run_system(system_config, root_name, connection, received_refs, **kw)
