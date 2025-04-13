import logging
import uuid
from concurrent.futures import Future
from functools import partial

from hyperapp.boot.htypes import HException

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    )

log = logging.getLogger(__name__)


DEFAULT_TIMEOUT = 10


def _param_value_to_ref(value):
    t = deduce_t(value)
    if type(value) is list:
        value = tuple(value)
    return mosaic.put(value, t)


def rpc_submit_target_factory(transport, rpc_request_futures, receiver_peer, sender_identity):

    def submit(target):
        request_id = str(uuid.uuid4())
        request = htypes.rpc.request(
            request_id=request_id,
            target=mosaic.put(target),
            )
        request_ref = mosaic.put(request)
        future = Future()
        rpc_request_futures[request_id] = future
        log.info("Rpc call target: receiver=%s: send rpc request %s: %s", receiver_peer, request_ref, request)
        transport.send(receiver_peer, sender_identity, [request_ref])
        return future

    return submit


class RpcServantWrapper:

    def __init__(self):
        self._wrapper = None

    def set(self, wrapper):
        self._wrapper = wrapper

    def reset(self):
        self._wrapper = None

    def wrap(self, servant_ref, kw):
        if self._wrapper is None:
            return (servant_ref, kw)
        return self._wrapper(servant_ref, kw)


class RpcSystemServantWrapper:

    def __init__(self):
        self._wrapper = None
        self._rpc_system_call_factory = None

    def set(self, wrapper, rpc_system_call_factory):
        self._wrapper = wrapper
        self._rpc_system_call_factory = rpc_system_call_factory

    def reset(self):
        self._wrapper = None
        self._rpc_system_call_factory = None

    def wrap(self, fn, kw):
        if self._wrapper is None:
            return (fn, kw)
        return self._wrapper(rpc_system_call_factory, fn, kw)


class RpcServiceWrapper:

    def __init__(self):
        self._wrapper = None

    def set(self, wrapper):
        self._wrapper = wrapper

    def reset(self):
        self._wrapper = None

    def wrap(self, service_name, kw):
        if self._wrapper is None:
            return (service_name, kw)
        return self._wrapper(service_name, kw)


def _kw_to_params(kw):
    return tuple(
        htypes.rpc.param(
            name=name,
            value=_param_value_to_ref(value),
            )
        for name, value in kw.items()
        )


def rpc_submit_factory(rpc_submit_target_factory, rpc_servant_wrapper, receiver_peer, sender_identity, servant_ref):
    submit_factory = rpc_submit_target_factory(receiver_peer, sender_identity)

    def submit(**kw):
        wrapped_servant_ref, wrapped_kw = rpc_servant_wrapper.wrap(servant_ref, kw)
        params = _kw_to_params(wrapped_kw)
        target = htypes.rpc.function_target(
            servant_ref=wrapped_servant_ref,
            params=params,
            )
        log.info("Rpc call: receiver=%s servant=%s (%s): send rpc request: %s",
                 receiver_peer, wrapped_servant_ref, wrapped_kw, target)
        return submit_factory(target)

    return submit


def rpc_system_fn_submit_factory(rpc_submit_target_factory, rpc_system_servant_wrapper, receiver_peer, sender_identity, fn):
    submit_factory = rpc_submit_target_factory(receiver_peer, sender_identity)

    def submit(**kw):
        wrapped_fn, wrapped_kw = rpc_system_servant_wrapper.wrap(fn, kw)
        params = _kw_to_params(wrapped_kw)
        target = htypes.rpc.system_fn_target(
            fn=mosaic.put(wrapped_fn.piece),
            params=params,
            )
        log.info("Rpc system call: receiver=%s fn=%s (%s): send rpc request: %s",
                 receiver_peer, wrapped_fn.piece, wrapped_kw, target)
        return submit_factory(target)

    return submit


def service_submit_factory(rpc_submit_target_factory, rpc_service_wrapper, receiver_peer, sender_identity, service_name):
    submit_factory = rpc_submit_target_factory(receiver_peer, sender_identity)

    def submit(**kw):
        wrapped_service_name, wrapped_kw = rpc_service_wrapper.wrap(service_name, kw)
        params = _kw_to_params(wrapped_kw)
        target = htypes.rpc.service_target(
            service_name=wrapped_service_name,
            params=params,
            )
        log.info("Rpc service call: receiver=%s service=%r (%s): send rpc request: %s",
                 receiver_peer, wrapped_service_name, wrapped_kw, target)
        return submit_factory(target)

    return submit


def rpc_wait_for_future(future, timeout_sec):
    try:
        result = future.result(timeout_sec)
    except HException as x:
        if isinstance(x, htypes.rpc.server_error):
            log.error("Rpc call: got server error: %s\n%s", x.message, "".join(x.traceback))
        raise
    log.info("Rpc call: got result: %s", result)
    return result


def rpc_call_factory(rpc_submit_factory, rpc_wait_for_future, receiver_peer, sender_identity, servant_ref, timeout_sec=DEFAULT_TIMEOUT):
    submit_factory = rpc_submit_factory(receiver_peer, sender_identity, servant_ref)
    def call(**kw):
        future = submit_factory(**kw)
        return rpc_wait_for_future(future, timeout_sec)
    return call


def rpc_system_call_factory(rpc_system_fn_submit_factory, rpc_wait_for_future, receiver_peer, sender_identity, fn, timeout_sec=DEFAULT_TIMEOUT):
    submit_factory = rpc_system_fn_submit_factory(receiver_peer, sender_identity, fn)
    def call(**kw):
        future = submit_factory(**kw)
        return rpc_wait_for_future(future, timeout_sec)
    return call


def service_call_factory(service_submit_factory, rpc_wait_for_future, receiver_peer, sender_identity, service_name, timeout_sec=DEFAULT_TIMEOUT):
    submit_factory = service_submit_factory(receiver_peer, sender_identity, service_name)
    def call(**kw):
        future = submit_factory(**kw)
        return rpc_wait_for_future(future, timeout_sec)
    return call
