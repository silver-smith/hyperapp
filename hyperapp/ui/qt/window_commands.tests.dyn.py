from unittest.mock import Mock

from .fixtures import qapp_fixtures
from .tested.code import window_commands


def test_quit(qapp):
    hook = Mock()
    window_commands.quit(hook)
