import logging

_log = logging.getLogger(__name__)


from .services import web
from . import services

_log.info(f"{services=}")
_log.info(f"{services.web=}")
_log.info(f"{web=}")

assert hasattr(services.web, 'pull')
assert hasattr(web, 'pull')
assert services.web is web

from .services import file_bundle
_log.info(f"{file_bundle=}")


from . import htypes

_log.info(f"{htypes=}")
_log.info(f"{htypes.impl=}")
_log.info(f"{htypes.impl.list_spec=}")
assert htypes.impl.list_spec.name == 'list_spec'
assert 'dir' in htypes.impl.list_spec.fields

from .htypes.impl import list_spec

assert list_spec is htypes.impl.list_spec

from .htypes import impl

assert impl.list_spec is htypes.impl.list_spec


from . import meta_registry
_log.info(f"{meta_registry=}")


def test_fn():
    pass


from . import lcs
_log.info(f"{lcs=}")
_log.info(f"{lcs.LCSheet=}")

from .qt_keys import run_input_key_dialog

_log.info("Loaded: auto_importer_module")
