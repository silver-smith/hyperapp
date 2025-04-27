from .code.mark import mark


@mark.global_command
def hello_world():
    return "Hello, world!"
