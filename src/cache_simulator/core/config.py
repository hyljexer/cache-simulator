from dataclasses import dataclass
from enum import Enum


class MappingType(Enum):
    DIRECT_MAPPED = "direct_mapped"
    SET_ASSOCIATIVE = "set_associative"
    FULLY_ASSOCIATIVE = "fully_associative"


class ReplacementPolicyType(Enum):
    LRU = "lru"
    FIFO = "fifo"
    LFU = "lfu"
    RANDOM = "random"


def _is_power_of_two(value: int) -> bool:
    return value > 0 and (value & (value - 1) == 0)


@dataclass(frozen=True)
class CacheConfig:
    cache_size: int  # cache size in bytes
    block_size: int  # size of one line in bytes
    associativity: int
    policy: ReplacementPolicyType = ReplacementPolicyType.LRU
    address_bits: int = 32  # address width

    def __post_init__(self) -> None:
        if not _is_power_of_two(self.cache_size):
            raise ValueError("cache_size must be a positive power of 2")
        if not _is_power_of_two(self.block_size):
            raise ValueError("block_size must be a positive power of 2")
        if not _is_power_of_two(self.associativity):
            raise ValueError("associativity must be a positive power of 2")
        if self.address_bits <= 0:
            raise ValueError("address_bits must be positive")
        if self.block_size > self.cache_size:
            raise ValueError("block_size cannot be larger than cache_size")
        if self.associativity > self.num_lines:
            raise ValueError("associativity cannot exceed total number of cache lines")
        if self.index_bits + self.offset_bits > self.address_bits:
            raise ValueError("cache geometry exceeds address space")

    @property
    def num_lines(self) -> int:
        return self.cache_size // self.block_size

    @property
    def num_sets(self) -> int:
        return self.num_lines // self.associativity

    @property
    def offset_bits(self) -> int:
        return self.block_size.bit_length() - 1

    @property
    def index_bits(self) -> int:
        return self.num_sets.bit_length() - 1

    @property
    def tag_bits(self) -> int:
        return self.address_bits - self.index_bits - self.offset_bits

    @property
    def mapping_type(self) -> MappingType:
        if self.associativity == 1:
            return MappingType.DIRECT_MAPPED
        if self.associativity == self.num_lines:
            return MappingType.FULLY_ASSOCIATIVE
        return MappingType.SET_ASSOCIATIVE
