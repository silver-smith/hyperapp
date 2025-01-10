from pathlib import Path

from .tested.code import file_bundle as tested_module


def test_file_bundle_service(file_bundle):
    bundle = file_bundle(Path('/tmp/test_file_bundle_service.cdr'), encoding='cdr')
