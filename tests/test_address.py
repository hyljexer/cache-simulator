import pytest

from cache_simulator.core.address import AddressDecoder
from cache_simulator.core.config import CacheConfig


def test_decode_set_associative() -> None:
    # 16-bit: tag=9 bits, index=3 bits, offset=4 bits
    # 0x1A5C = 000110100_101_1100 -> tag=0x34 (52), index=5, offset=0xC (12)
    cfg = CacheConfig(cache_size=256, block_size=16, associativity=2, address_bits=16)
    decoder = AddressDecoder(cfg)

    decoded = decoder.decode(0x1A5C)

    assert decoded.raw == 0x1A5C
    assert decoded.tag == 0x34
    assert decoded.index == 5
    assert decoded.offset == 0xC
    assert decoded.block_address == 0x1A5


def test_decode_direct_mapped() -> None:
    # 16-bit: tag=8 bits, index=4 bits, offset=4 bits
    cfg = CacheConfig(cache_size=256, block_size=16, associativity=1, address_bits=16)
    decoder = AddressDecoder(cfg)

    decoded = decoder.decode(0x1A5C)

    assert decoded.tag == 0x1A
    assert decoded.index == 0x5
    assert decoded.offset == 0xC


def test_decode_fully_associative_has_zero_index() -> None:
    # 16-bit: tag=12 bits, index=0 bits, offset=4 bits
    cfg = CacheConfig(cache_size=256, block_size=16, associativity=16, address_bits=16)
    decoder = AddressDecoder(cfg)

    decoded = decoder.decode(0x1A5C)

    assert decoded.tag == 0x1A5
    assert decoded.index == 0
    assert decoded.offset == 0xC


def test_decode_out_of_range_raises_error() -> None:
    cfg = CacheConfig(cache_size=256, block_size=16, associativity=1, address_bits=16)
    decoder = AddressDecoder(cfg)

    with pytest.raises(ValueError, match="out of range"):
        decoder.decode(0x10000)  # first address above 16 bits
