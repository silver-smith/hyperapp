import logging
import traceback
import threading
import asyncio

from hyperapp.common.ref import encode_bundle, decode_bundle, decode_capsule
from hyperapp.common.interface import phony_transport as phony_transport_types
from ..module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.phony'


class Transport(object):

    def __init__(self, ref_collector_factory, request_queue):
        self._ref_collector_factory = ref_collector_factory
        self._request_queue = request_queue

    def send(self, message_ref):
        ref_collector = self._ref_collector_factory()
        bundle = ref_collector.make_bundle([message_ref])
        log.debug('phony transport: enqueueing request bundle')
        self._request_queue.put(encode_bundle(bundle))


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        self._event_loop = services.event_loop
        self._response_queue = services.response_queue
        self._types = services.types
        self._unbundler = services.unbundler
        self._ref_resolver = services.ref_resolver
        self._remoting = services.remoting
        self._queue_thread = threading.Thread(
            target=self._queue_thread_main)
        services.transport_registry.register(
            phony_transport_types.server_address,
            self._resolve_address,
            services.ref_collector_factory,
            services.request_queue,
            )
        services.on_start.append(self._start_queue_thread)
        services.on_stop.append(self._stop_queue_thread)

    def _resolve_address(self, address_ref, address, ref_collector_factory, request_queue):
        return Transport(ref_collector_factory, request_queue)

    def _start_queue_thread(self):
        self._queue_thread.start()

    def _stop_queue_thread(self):
        self._response_queue.put(None)
        self._queue_thread.join()

    def _queue_thread_main(self):
        while True:
            log.debug('phony transport: waiting for message bundle...')
            encoded_message_bundle = self._response_queue.get()
            if not encoded_message_bundle:
                log.debug('phony transport: message queue thread is finished.')
                break
            log.debug('phony transport: scheduling message bundle')
            asyncio.run_coroutine_threadsafe(self._process_message_bundle(encoded_message_bundle), self._event_loop)

    async def _process_message_bundle(self, encoded_message_bundle):
        try:
            log.debug('phony transport: processing message bundle...')
            rpc_message_bundle = decode_bundle(encoded_message_bundle)
            self._unbundler.register_bundle(rpc_message_bundle)
            assert len(rpc_message_bundle.roots) == 1
            rpc_message_capsule = self._ref_resolver.resolve_ref(rpc_message_bundle.roots[0])
            rpc_message = decode_capsule(self._types, rpc_message_capsule)
            self._remoting.process_rpc_message(rpc_message_bundle.roots[0], rpc_message)
            log.debug('phony transport: processing message bundle: done')
        except:
            traceback.print_exc()  # traceback is not shown when scheduled by run_coroutine_threadsafe
