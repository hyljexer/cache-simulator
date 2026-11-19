import pytest

from cache_simulator.core.cache import Cache
from cache_simulator.core.config import CacheConfig, ReplacementPolicyType


def test_direct_mapped_conflict_miss() -> None:
    # 4 linie, 4 zbiory, blok 16B -> adresy 0x0000 i 0x0040 trafiają do tego samego zbioru 0
    cfg = CacheConfig(cache_size=64, block_size=16, associativity=1, address_bits=16)
    cache = Cache(cfg)

    e1 = cache.read(0x0000)  # miss (ładuje tag 0 do zbioru 0)
    e2 = cache.read(0x0004)  # hit (ten sam blok!)
    e3 = cache.read(0x0040)  # miss + eviction (tag 1 wyrzuca tag 0)
    e4 = cache.read(0x0000)  # miss + eviction (tag 0 wyrzuca tag 1 -> "ping-pong")

    assert e1.hit is False and e1.evicted is False
    assert e2.hit is True
    assert e3.hit is False and e3.evicted is True and e3.evicted_tag == 0
    assert e4.hit is False and e4.evicted is True and e4.evicted_tag == 1

    assert cache.stats.total_accesses == 4
    assert cache.stats.hits == 1
    assert cache.stats.misses == 3
    assert cache.stats.evictions == 2
    assert cache.stats.hit_rate == pytest.approx(0.25)


def test_set_associative_eliminates_conflict_miss() -> None:
    # Ten sam rozmiar cache (64B), ale 2-way (2 zbiory po 2 linie)
    cfg = CacheConfig(cache_size=64, block_size=16, associativity=2, address_bits=16)
    cache = Cache(cfg)

    cache.read(0x0000)  # miss -> zbiór 0, linia 0
    cache.read(0x0040)  # miss -> zbiór 0, linia 1 (bez wyrzucania!)
    e3 = cache.read(0x0000)  # hit!
    e4 = cache.read(0x0040)  # hit!

    assert e3.hit is True
    assert e4.hit is True
    assert cache.stats.evictions == 0
    assert cache.stats.hit_rate == pytest.approx(0.5)


def test_fully_associative_lru_vs_fifo() -> None:
    # 2 linie w 1 zbiorze (Fully Associative), bloki po 16B
    lru_cfg = CacheConfig(
        cache_size=32,
        block_size=16,
        associativity=2,
        policy=ReplacementPolicyType.LRU,
        address_bits=16,
    )
    fifo_cfg = CacheConfig(
        cache_size=32,
        block_size=16,
        associativity=2,
        policy=ReplacementPolicyType.FIFO,
        address_bits=16,
    )

    lru_cache = Cache(lru_cfg)
    fifo_cache = Cache(fifo_cfg)

    sequence = [0x0000, 0x0010, 0x0000, 0x0020, 0x0000]
    lru_hits = [lru_cache.read(addr).hit for addr in sequence]
    fifo_hits = [fifo_cache.read(addr).hit for addr in sequence]

    # W LRU ostatni dostęp do 0x0000 jest HIT (bo wcześniej 0x0000 odświeżono, wyleciał 0x0010)
    assert lru_hits == [False, False, True, False, True]
    # W FIFO ostatni dostęp do 0x0000 jest MISS (bo 0x0000 włożono jako pierwszy i wyleciał)
    assert fifo_hits == [False, False, True, False, False]


def test_write_sets_dirty_flag_and_reset_clears_state() -> None:
    cfg = CacheConfig(cache_size=64, block_size=16, associativity=1, address_bits=16)
    cache = Cache(cfg)

    cache.write(0x0000)
    e2 = cache.read(0x0040)  # wypycha brudną linię 0x0000

    assert e2.evicted is True
    assert e2.dirty_eviction is True
    assert cache.stats.writes == 1
    assert cache.stats.reads == 1

    cache.reset()
    assert cache.stats.total_accesses == 0
    assert all(not line.valid for s in cache.sets for line in s.lines)
