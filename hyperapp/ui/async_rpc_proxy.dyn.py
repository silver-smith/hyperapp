from . import htypes


class AsyncRpcProxy:

    def __init__(self, async_rpc_call_factory, async_rpc_endpoint, identity, peer, servant_ref):
        self._async_rpc_call_factory = async_rpc_call_factory
        self._async_rpc_endpoint = async_rpc_endpoint
        self._identity = identity
        self._peer = peer
        self._servant_ref = servant_ref

    def __getattr__(self, name):
        fn_ref = htypes.attribute.attribute(
            object=self._servant_ref,
            attr_name=name,
            )
        rpc_call = self._async_rpc_call_factory(self._async_rpc_endpoint, self._peer, fn_ref, self._identity)

        async def method(*args, **kw):
            return await rpc_call(*args, **kw)

        return method
