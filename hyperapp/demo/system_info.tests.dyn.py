from .tested.code import system_info


def test_system_info():
    info = system_info.system_info()
    assert type(info) is list
