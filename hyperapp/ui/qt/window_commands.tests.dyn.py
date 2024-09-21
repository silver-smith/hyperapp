from .fixtures import qapp_fixtures
from .tested.code import window_commands


def test_quit(qapp):
    window_commands.quit()
