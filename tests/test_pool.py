from game.pool import ObjectPool


class _Dummy:
    def __init__(self):
        self.active = False


def test_get_reuses_an_inactive_object():
    pool = ObjectPool(_Dummy, initial_size=3)
    first = pool.get()
    assert first in pool.pool
    assert len(pool.pool) == 3


def test_get_grows_the_pool_when_all_objects_are_active():
    pool = ObjectPool(_Dummy, initial_size=2)
    for obj in pool.pool:
        obj.active = True

    grown = pool.get()

    assert len(pool.pool) == 3
    assert grown in pool.pool
    assert grown.active is False
