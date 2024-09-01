
def ui_command_marker(t, module_name):
    def _ui_command_wrapper(fn):
        return fn
    return _ui_command_wrapper


def ui_model_command_marker(t, module_name):
    def _ui_command_wrapper(fn):
        return fn
    return _ui_command_wrapper
