from .tested.code import editor_defaults


def test_string_default():
    value = editor_defaults.string_default()
    assert value == ""
