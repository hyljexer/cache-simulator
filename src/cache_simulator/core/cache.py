import random
from dataclasses import dataclass

from cache_simulator.core.address import AddressDecoder
from cache_simulator.core.config import CacheConfig
from cache_simulator.core.policies import ReplacementPolicy, create_replacement_policy
from cache_simulator.core.trace import (
    CacheStats,
    MemoryOperation,
    OperationType,
    StepEvent,
)


@dataclass
class CacheLine:
    valid: bool = False
    dirty: bool = False
    tag: int = 0
    block_address: int | None = None


class CacheSet:
    def __init__(self, associativity: int, policy: ReplacementPolicy) -> None:
        self.lines: list[CacheLine] = [CacheLine() for _ in range(associativity)]
        self.policy: ReplacementPolicy = policy

    def find_line(self, tag: int) -> int | None:
        for way_index, line in enumerate(self.lines):
            if line.valid and line.tag == tag:
                return way_index
        return None

    def find_empty_line(self) -> int | None:
        for way_index, line in enumerate(self.lines):
            if not line.valid:
                return way_index
        return None

    def reset(self) -> None:
        for line in self.lines:
            line.valid = False
            line.dirty = False
            line.tag = 0
            line.block_address = None
        self.policy.reset()


class Cache:
    def __init__(self, config: CacheConfig, seed: int | None = None) -> None:
        self.config = config
        self._decoder = AddressDecoder(config)
        self._rng = random.Random(seed) if seed is not None else None
        self._sets: list[CacheSet] = [
            CacheSet(
                associativity=config.associativity,
                policy=create_replacement_policy(config.policy, rng=self._rng),
            )
            for _ in range(config.num_sets)
        ]
        self._stats = CacheStats()

    @property
    def sets(self) -> tuple[CacheSet, ...]:
        return tuple(self._sets)

    @property
    def stats(self) -> CacheStats:
        return self._stats

    def read(self, address: int) -> StepEvent:
        return self.access(MemoryOperation(OperationType.READ, address))

    def write(self, address: int) -> StepEvent:
        return self.access(MemoryOperation(OperationType.WRITE, address))

    def access(self, operation: MemoryOperation) -> StepEvent:
        decoded = self._decoder.decode(operation.address)
        cache_set = self._sets[decoded.index]

        if operation.op_type == OperationType.READ:
            self._stats.reads += 1
        else:
            self._stats.writes += 1

        hit_way = cache_set.find_line(decoded.tag)

        # CACHE HIT
        if hit_way is not None:
            self._stats.hits += 1
            if operation.op_type == OperationType.WRITE:
                cache_set.lines[hit_way].dirty = True
            cache_set.policy.on_access(hit_way)

            return StepEvent(
                step_number=self._stats.total_accesses,
                operation=operation,
                decoded=decoded,
                hit=True,
                set_index=decoded.index,
                way_index=hit_way,
                evicted=False,
            )

        # CACHE MISS
        self._stats.misses += 1
        empty_way = cache_set.find_empty_line()

        if empty_way is not None:
            target_way = empty_way
            evicted = False
            evicted_tag = None
            evicted_block = None
            dirty_eviction = False
        else:
            target_way = cache_set.policy.select_victim()
            victim = cache_set.lines[target_way]
            evicted = True
            evicted_tag = victim.tag
            evicted_block = victim.block_address
            dirty_eviction = victim.dirty
            self._stats.evictions += 1

        target_line = cache_set.lines[target_way]
        target_line.valid = True
        target_line.tag = decoded.tag
        target_line.block_address = decoded.block_address
        target_line.dirty = operation.op_type == OperationType.WRITE

        cache_set.policy.on_insert(target_way)

        return StepEvent(
            step_number=self._stats.total_accesses,
            operation=operation,
            decoded=decoded,
            hit=False,
            set_index=decoded.index,
            way_index=target_way,
            evicted=evicted,
            evicted_tag=evicted_tag,
            evicted_block_address=evicted_block,
            dirty_eviction=dirty_eviction,
        )

    def reset(self) -> None:
        for cache_set in self._sets:
            cache_set.reset()
        self._stats = CacheStats()
