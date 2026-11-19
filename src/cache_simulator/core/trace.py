from dataclasses import dataclass
from enum import Enum

from cache_simulator.core.address import DecodedAddress


class OperationType(Enum):
    READ = "r"
    WRITE = "w"


@dataclass(frozen=True)
class MemoryOperation:
    op_type: OperationType
    address: int


@dataclass(frozen=True)
class StepEvent:
    step_number: int
    operation: MemoryOperation
    decoded: DecodedAddress
    hit: bool
    set_index: int
    way_index: int
    evicted: bool
    evicted_tag: int | None = None
    evicted_block_address: int | None = None
    dirty_eviction: bool = False


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    reads: int = 0
    writes: int = 0
    evictions: int = 0

    @property
    def total_accesses(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        total = self.total_accesses
        return self.hits / total if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        total = self.total_accesses
        return self.misses / total if total > 0 else 0.0
