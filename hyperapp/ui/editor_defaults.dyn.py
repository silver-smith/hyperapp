from .code.mark import mark


@mark.editor.default
def string_default():
    return ""
