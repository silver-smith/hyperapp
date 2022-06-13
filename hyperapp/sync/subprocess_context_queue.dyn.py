import queue


def runner_signal_queue():
    return queue.Queue()


def runner_is_ready(runner_peer_ref, queue):
    queue.put(runner_peer_ref)
