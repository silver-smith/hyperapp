import logging
import threading
import asyncio

from hyperapp.common.ref import encode_bundle, decode_bundle
from hyperapp.client.module import ClientModule
from . import htypes

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.phony'


class Transport(object):

    def __init__(self, ref_collector_factory, request_queue):
        self._ref_collector_factory = ref_collector_factory
        self._request_queue = request_queue

    def send(self, message_ref):
        ref_collector = self._ref_collector_factory()
        bundle = ref_collector.make_bundle([message_ref])
        log.debug('Phony transport: enqueueing request bundle')
        self._request_queue.put(encode_bundle(bundle))


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        self._event_loop = services.event_loop
        self._response_queue = services.response_queue
        self._ref_resolver = services.ref_resolver
        self._type_resolver = services.type_resolver
        self._unbundler = services.unbundler
        self._remoting = services.remoting
        self._queue_thread = threading.Thread(
            target=self._queue_thread_main)
        server_address_type_ref = services.type_resolver.reverse_resolve(htypes.phony_transport.server_address)
        services.transport_registry.register_type_ref(
            server_address_type_ref,
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
            log.debug('Phony transport: waiting for message bundle...')
            encoded_message_bundle = self._response_queue.get()
            if not encoded_message_bundle:
                log.debug('Phony transport: message queue thread is finished.')
                break
            log.debug('Phony transport: scheduling message bundle')
            asyncio.run_coroutine_threadsafe(self._process_message_bundle(encoded_message_bundle), self._event_loop)

    async def _process_message_bundle(self, encoded_message_bundle):
        try:
            log.debug('Phony transport: processing message bundle...')
            rpc_message_bundle = decode_bundle(encoded_message_bundle)
            self._unbundler.register_bundle(rpc_message_bundle)
            assert len(rpc_message_bundle.roots) == 1
            rpc_message_capsule = self._ref_resolver.resolve_ref(rpc_message_bundle.roots[0])
            rpc_message = decode_capsule(self._types, rpc_message_capsule)
            self._remoting.process_rpc_message(rpc_message_bundle.roots[0], rpc_message)
            log.debug('Phony transport: processing message bundle: done')
        except:
            # traceback is not shown when scheduled by run_coroutine_threadsafe
            log.exception('Phony transport: error processing message bundle:')
