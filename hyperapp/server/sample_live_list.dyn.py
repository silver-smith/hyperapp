import logging
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class LiveListServant:

    def __init__(self, mosaic, peer_registry, rpc_call_factory, identity, rpc_endpoint, executor):
        self._mosaic = mosaic
        self._peer_registry = peer_registry
        self._rpc_call_factory = rpc_call_factory
        self._identity = identity
        self._rpc_endpoint = rpc_endpoint
        self._executor = executor

    def list(self, request, peer_ref, servant_ref):
        peer = self._peer_registry.invite(peer_ref)
        log.info("LiveListServant.list(%s, %s)", peer, servant_ref)
        self._executor.submit(partial(self._send_diffs, peer, servant_ref))
        return [
            htypes.sample_list.row(idx, f"Row #{idx}")
            for idx in range(20)
            if idx % 10 != 9
            ]

    def describe(self, request, current_key):
        log.info("LiveListServant.describe(%r)", current_key)
        return "Opened item: {}".format(current_key)

    def raw(self, request, current_key):
        log.info("LiveListServant.raw(%r)", current_key)
        return htypes.sample_list.article(
            title=f"Article {current_key}",
            text=f"Sample contents for:\n{current_key}",
            )

    def _send_diffs(self, peer, servant_ref):
        try:
            rpc_call = self._rpc_call_factory(self._rpc_endpoint, peer, servant_ref, self._identity)
            for idx in range(20):
                if idx % 5 != 4:
                    continue
                time.sleep(1)
                item = htypes.sample_list.row(idx, f"Row #{idx} by diff")
                if idx % 10 == 9:
                    remove_key_list = []
                else:
                    remove_key_list = [self._mosaic.put(idx)]
                diff = htypes.service.list_diff(
                    remove_key_list=remove_key_list,
                    item_list=[self._mosaic.put(item)],
                    )
                log.info("Send diffs #%d: %s", idx, diff)
                rpc_call(diff)
        except Exception as x:
            log.exception("Error sending diff:")


def executor():
    return ThreadPoolExecutor()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        server_ref_list_piece = services.resource_module_registry['server.server_ref_list']['server_ref_list']
        server_ref_list = services.python_object_creg.animate(server_ref_list_piece)

        sample_list_module = services.resource_module_registry['server.sample_live_list']
        sample_list_service_piece = sample_list_module['sample_list_service']
        sample_list_service = services.python_object_creg.animate(sample_list_service_piece)
        server_ref_list.add_ref('sample_live_list', 'Sample live list', mosaic.put(sample_list_service))

        self._python_object_creg = services.python_object_creg
        self._executor_piece = sample_list_module['executor']

        services.on_stop.append(self.stop)

    def stop(self):
        executor = self._python_object_creg.animate(self._executor_piece)
        executor.shutdown()
