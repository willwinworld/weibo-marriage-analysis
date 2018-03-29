import redis
import functools
from redis_queue import RedisQueue

conn = redis.Redis(host='127.0.0.1', port='6379', password='', db=1)


def pipe(src, dst=None):
    src_q = RedisQueue(src, conn=conn)
    if dst:
        dst_q = RedisQueue(dst, conn=conn)

    def outer(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            ret = None
            while not src_q.empty():
                try:
                    kwargs['param'] = src_q.get()
                except Exception as err:
                    print(err)
                    raise Exception('Get element from redis %s timeout!' % src_q.key)
                try:
                    ret = func(*args, **kwargs)
                except Exception as err:
                    print(err)
                    src_q.put(kwargs['param'])
                if dst:
                    if isinstance(ret, list):
                        for r in ret:
                            dst_q.put(r)
                    else:
                        dst_q.put(ret)
            return ret

        return inner

    return outer
