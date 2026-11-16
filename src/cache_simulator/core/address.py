from dataclasses import dataclass

from cache_simulator.core.config import CacheConfig


@dataclass(frozen=True)
class DecodedAddress:
    raw: int
    tag: int
    index: int
    offset: int
    block_address: int


class AddressDecoder:
    def __init__(self, config: CacheConfig) -> None:
        self._address_bits = config.address_bits
        self._offset_bits = config.offset_bits
        self._index_bits = config.index_bits
        self._max_address = (1 << config.address_bits) - 1

        self._offset_mask = (1 << self._offset_bits) - 1
        self._index_mask = (1 << self._index_bits) - 1

    def decode(self, address: int) -> DecodedAddress:
        if address < 0 or address > self._max_address:
            raise ValueError(
                f"Address {address:#x} out of range for {self._address_bits}-bit space"
            )
        offset = address & self._offset_mask
        index = (address >> self._offset_bits) & self._index_mask
        tag = address >> (self._offset_bits + self._index_bits)
        block_address = address >> self._offset_bits

        return DecodedAddress(
            raw=address,
            tag=tag,
            index=index,
            offset=offset,
            block_address=block_address,
        )
