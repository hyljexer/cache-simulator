import pytest

from cache_simulator.core.config import CacheConfig, MappingType


def test_direct_mapped_geometry() -> None:
    cfg = CacheConfig(cache_size=256, block_size=16, associativity=1, address_bits=16)

    assert cfg.num_lines == 16
    assert cfg.num_sets == 16
    assert cfg.offset_bits == 4
    assert cfg.index_bits == 4
    assert cfg.tag_bits == 8
    assert cfg.mapping_type == MappingType.DIRECT_MAPPED


def test_set_associative_geometry() -> None:
    cfg = CacheConfig(cache_size=256, block_size=16, associativity=2, address_bits=16)

    assert cfg.num_lines == 16
    assert cfg.num_sets == 8
    assert cfg.offset_bits == 4
    assert cfg.index_bits == 3
    assert cfg.tag_bits == 9
    assert cfg.mapping_type == MappingType.SET_ASSOCIATIVE


def test_fully_associative_geometry() -> None:
    cfg = CacheConfig(cache_size=256, block_size=16, associativity=16, address_bits=16)

    assert cfg.num_lines == 16
    assert cfg.num_sets == 1
    assert cfg.offset_bits == 4
    assert cfg.index_bits == 0
    assert cfg.tag_bits == 12
    assert cfg.mapping_type == MappingType.FULLY_ASSOCIATIVE


def test_invalid_cache_size_raises_error() -> None:
    with pytest.raises(ValueError, match="power of 2"):
        CacheConfig(cache_size=300, block_size=16, associativity=1)


def test_associativity_exceeding_lines_raises_error() -> None:
    with pytest.raises(ValueError, match="exceed total number of cache lines"):
        CacheConfig(cache_size=64, block_size=16, associativity=8)
