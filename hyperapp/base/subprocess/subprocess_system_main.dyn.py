from .code.system import System


def system_main(connection, received_refs, system_config_piece, root_name, **kw):
    system = System()
    system.load_config(system_config_piece)
    system['init_hook'].run_hooks()
    system.run(root_name, connection, received_refs, **kw)
