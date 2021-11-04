import logging
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from hyperapp.common.module import Module

from . import htypes
from .item_column_list import item_t_to_column_list

log = logging.getLogger(__name__)


class LiveListServant:

    def __init__(self, mosaic, peer_registry, servant_path_from_data, rpc_call_factory, identity, rpc_endpoint, executor):
        self._mosaic = mosaic
        self._peer_registry = peer_registry
        self._servant_path_from_data = servant_path_from_data
        self._rpc_call_factory = rpc_call_factory
        self._identity = identity
        self._rpc_endpoint = rpc_endpoint
        self._executor = executor

    def list(self, request, peer_ref, servant_path_data):
        peer = self._peer_registry.invite(peer_ref)
        servant_path = self._servant_path_from_data(servant_path_data)
        log.info("LiveListServant.list(%s, %s)", peer, servant_path)
        self._executor.submit(partial(self._send_diffs, peer, servant_path))
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

    def _send_diffs(self, peer, servant_path):
        try:
            rpc_call = self._rpc_call_factory(self._rpc_endpoint, peer, servant_path, self._identity)
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


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        mosaic = services.mosaic

        server_peer_ref = mosaic.put(services.server_identity.peer.piece)

        list_servant_name = 'sample_live_list_servant'
        list_servant_path = services.servant_path().registry_name(list_servant_name)

        describe_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=list_servant_path.get_attr('describe').as_data,
            state_attr_list=['current_key'],
            name='describe',
            )
        raw_command = htypes.rpc_command.rpc_command(
            peer_ref=server_peer_ref,
            servant_path=list_servant_path.get_attr('raw').as_data,
            state_attr_list=['current_key'],
            name='raw',
            )
        list_service = htypes.service.live_list_service(
            peer_ref=server_peer_ref,
            servant_path=list_servant_path.get_attr('list').as_data,
            dir_list=[[mosaic.put(htypes.sample_list.sample_live_list_d())]],
            command_ref_list=[
                mosaic.put(describe_command),
                mosaic.put(raw_command),
                ],
            key_column_id='key',
            column_list=item_t_to_column_list(services.types, htypes.sample_list.row),
            )

        self._executor = ThreadPoolExecutor()

        list_servant = LiveListServant(
            services.mosaic,
            services.peer_registry,
            services.servant_path_from_data,
            services.rpc_call_factory,
            services.server_identity,
            services.server_rpc_endpoint,
            self._executor,
            )
        services.server_rpc_endpoint.register_servant(list_servant_name, list_servant)

        services.server_ref_list.add_ref('sample_live_list', 'Sample live list', mosaic.put(list_service))

        services.on_stop.append(self.stop)

    def stop(self):
        self._executor.shutdown()
