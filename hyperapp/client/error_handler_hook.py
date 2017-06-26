
# may be we can get rid of this hook as we are using intermediate handle now

_error_handler = None

def get_handle_for_error(exception):
    global _error_handler
    if _error_handler:
        return _error_handler(exception)
    else:
        return None

def set_error_handler(handler):
    global _error_handler
    _error_handler = handler
