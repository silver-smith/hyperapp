from .tested.code import hello_world


def test_hello_world():
    greeting = hello_world.hello_world()
    assert type(greeting) is str
