
# decorator for View, ClientModule and Object methods
def command(class_method):
    class_method.__is_command__ = True
    return class_method
