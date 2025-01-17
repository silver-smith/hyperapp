from .code.system import run_config


def system_main(connection, received_refs, system_config_piece, root_name, **kw):
    run_config(system_config_piece, root_name, connection, received_refs, **kw)
