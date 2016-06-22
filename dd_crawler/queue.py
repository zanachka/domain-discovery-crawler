import random
from urllib.parse import urlsplit
from zlib import crc32
from typing import Tuple
import logging

import scrapy
from scrapy_redis.queue import Base


logger = logging.getLogger(__name__)


class RequestQueue(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.len_key = '{}:len'.format(self.key)
        self.queues_key = '{}:queues'.format(self.key)
        self.workers_key = '{}:workers'.format(self.key)
        self.worker_id_key = '{}:worker-id'.format(self.key)
        self.worker_id = self.server.incr(self.worker_id_key)
        self.alive_timeout = 10  # seconds
        self.im_alive()

    def __len__(self):
        return int(self.server.get(self.len_key) or '0')

    def push(self, request):
        data = self._encode_request(request)
        pairs = {data: -request.priority}
        queue_key = self.request_queue_key(request)
        added = self.server.zadd(queue_key, **pairs)
        if added:
            self.server.incr(self.len_key)
        self.server.sadd(self.queues_key, queue_key)

    def pop(self, timeout=0):
        queue_key = self.select_queue_key()
        if queue_key:
            return self.pop_from_queue(queue_key)

    def clear(self):
        keys = {
            self.len_key, self.queues_key, self.workers_key, self.worker_id_key}
        keys.update(self.get_workers())
        keys.update(self.get_queues())
        self.server.delete(*keys)
        super().clear()

    def get_queues(self):
        return self.server.smembers(self.queues_key)

    def get_workers(self):
        return self.server.smembers(self.workers_key)

    def select_queue_key(self):
        """ Select which queue (domain) to use next.
        """
        idx, n_idx = self.discover()
        queues = self.get_queues()
        if queues:
            my_queues = [q for q in queues if crc32(q) % n_idx == idx]
            # TODO: select based on priority and available slots
            return random.choice(my_queues)

    def discover(self) -> Tuple[int, int]:
        """ Return a tuple of (my index, total number of workers).
        When workers connect or disconnect, this will cause re-distribution
        of domains between workers, but this is not an issue.
        """
        self.im_alive()
        worker_ids = set(map(int, self.get_workers()))
        for worker_id in list(worker_ids):
            if not self.is_alive(worker_id):
                self.server.srem(self.workers_key, worker_id)
                worker_ids.remove(worker_id)
        if self.worker_id in worker_ids:
            worker_ids = sorted(worker_ids)
            return worker_ids.index(self.worker_id), len(worker_ids)
        else:
            # This should not happen normally
            logger.warning('No live workers: selecting self!')
            return 0, 1

    def im_alive(self):
        pipe = self.server.pipeline()
        pipe.multi()
        pipe.sadd(self.workers_key, self.worker_id)\
            .set(self._worker_key(self.worker_id), 'ok', ex=self.alive_timeout)\
            .execute()

    def is_alive(self, worker_id):
        return bool(self.server.get(self._worker_key(worker_id)))

    def _worker_key(self, worker_id):
        return '{}:worker-{}'.format(self.key, worker_id)

    def pop_from_queue(self, queue_key):
        """ Pop value with highest priority from the given queue.
        """
        pipe = self.server.pipeline()
        pipe.multi()
        pipe.zrange(queue_key, 0, 0).zremrangebyrank(queue_key, 0, 0)
        results, count = pipe.execute()
        if results:
            self.server.decr(self.len_key)
            return self._decode_request(results[0])

    def request_queue_key(self, request):
        """ Key for request queue (based on it's domain).
        """
        domain = urlsplit(request.url).netloc
        return '{}:domain:{}'.format(self.key, domain)

    def get_stats(self):
        """ Return all queue stats.
        """
        queues = self.server.smembers(self.queues_key)
        return dict(
            len=len(self),
            n_domains=len(queues),
            queues={name: self.server.zcard(name) for name in queues},
        )


class CompactRequestQueue(RequestQueue):
    """ Queue with a more compact request representation:
    in our case, we need to preserve only url and priority.
    """

    def _encode_request(self, request):
        return '{} {}'.format(int(request.priority), request.url)

    def _decode_request(self, encoded_request):
        priority, url = encoded_request.decode('utf-8').split(' ', 1)
        return scrapy.Request(url, priority=int(priority))
