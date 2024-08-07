from . import htypes
from .services import (
    mosaic,
    )


class RpcProxy:

    def __init__(self, rpc_call_factory, rpc_endpoint, identity, peer, servant_ref, timeout_sec=10):
        self._rpc_call_factory = rpc_call_factory
        self._rpc_endpoint = rpc_endpoint
        self._identity = identity
        self._peer = peer
        self._servant_ref = servant_ref
        self._timeout_sec = timeout_sec

    def __getattr__(self, name):
        fn_res = htypes.builtin.attribute(
            object=self._servant_ref,
            attr_name=name,
            )
        fn_ref = mosaic.put(fn_res)
        rpc_call = rpc_call_factory(self._rpc_endpoint, self._peer, fn_ref, self._identity, self._timeout_sec)

        def method(*args, **kw):
            return rpc_call(*args, **kw)

        return method
