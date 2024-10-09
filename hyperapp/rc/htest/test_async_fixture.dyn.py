import logging
from unittest.mock import Mock

from .code.mark import mark
from .tested.code import sample_service_1 as sample_service_module_1

log = logging.getLogger(__name__)


@mark.fixture
async def async_fixture():
    log.info("Async fixture entered")
    return Mock(value='async-fixture')


@mark.fixture
def some_param():
    return 'some-param'


def test_fixture_sync(async_fixture):
    log.info("test_fixture_sync entered")
    assert async_fixture.value == 'async-fixture'
    log.info("test_fixture_sync finished")


async def test_fixture_async(async_fixture):
    log.info("test_fixture_async entered")
    assert async_fixture.value == 'async-fixture'
    log.info("test_fixture_async finished")


@mark.fixture
async def param_async_fixture(some_param):
    log.info("Param async fixture entered")
    return Mock(value='param-async-fixture')


def test_param_fixture_sync(param_async_fixture):
    log.info("test_param_fixture_sync entered")
    assert param_async_fixture.value == 'param-async-fixture'
    log.info("test_param_fixture_sync finished")


async def test_param_fixture_async(param_async_fixture):
    log.info("test_param_fixture_async entered")
    try:
        param_async_fixture.value
        assert False, "Exception is expected here"
    except RuntimeError as x:
        assert 'fixture.obj' in str(x)
    log.info("test_param_fixture_async finished")


@mark.fixture.obj
async def param_async_fixture_obj(some_param):
    log.info("Param async fixture obj entered")
    return Mock(value='param-async-fixture-obj')


def test_param_fixture_obj_sync(param_async_fixture_obj):
    log.info("test_param_fixture_obj_sync entered")
    assert param_async_fixture_obj.value == 'param-async-fixture-obj'
    log.info("test_param_fixture_obj_sync finished")


async def test_param_fixture_obj_async(param_async_fixture_obj):
    log.info("test_param_fixture_obj_async entered")
    assert param_async_fixture_obj.value == 'param-async-fixture-obj'
    log.info("test_param_fixture_obj_async finished")


@mark.fixture
async def async_gen():
    log.info("Async gen fixture entered")
    yield Mock(value='async-gen')
    log.info("Async gen fixture finalizer")


def test_gen_sync(async_gen):
    log.info("test_gen_sync entered")
    assert async_gen.value == 'async-gen'
    log.info("test_gen_sync finished")


async def test_gen_async(async_gen):
    log.info("test_gen_async entered")
    assert async_gen.value == 'async-gen'
    log.info("test_gen_async finished")


@mark.fixture
async def param_async_gen(some_param):
    log.info("Parameterized async gen fixture entered")
    yield Mock(value='param-async-gen')
    log.info("Parameterized async gen fixture finalizer")


def test_param_gen_sync(param_async_gen):
    log.info("test_param_gen_sync entered")
    assert param_async_gen.value == 'param-async-gen'
    log.info("test_param_gen_sync finished")


async def test_param_gen_async(param_async_gen):
    log.info("test_param_gen_async entered")
    try:
        param_async_gen.value
        assert False, "Exception is expected here"
    except RuntimeError as x:
        assert 'fixture.obj' in str(x)
    log.info("test_param_gen_async finished")


@mark.fixture.obj
async def param_async_gen_obj(some_param):
    log.info("Parameterized async gen fixture obj entered")
    yield Mock(value='param-async-gen-obj')
    log.info("Parameterized async gen fixture obj finalizer")


def test_param_gen_obj_sync(param_async_gen_obj):
    log.info("test_param_gen_obj_sync entered")
    assert param_async_gen_obj.value == 'param-async-gen-obj'
    log.info("test_param_gen_obj_sync finished")


async def test_param_gen_obj_async(param_async_gen_obj):
    log.info("test_param_gen_obj_async entered")
    assert param_async_gen_obj.value == 'param-async-gen-obj'
    log.info("test_param_gen_obj_async finished")
