import random
from abc import ABC, abstractmethod
from collections import OrderedDict

from cache_simulator.core.config import ReplacementPolicyType


class ReplacementPolicy(ABC):
    @abstractmethod
    def on_insert(self, way_index: int) -> None:
        pass

    @abstractmethod
    def on_access(self, way_index: int) -> None:
        pass

    @abstractmethod
    def select_victim(self) -> int:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass


class LRUPolicy(ReplacementPolicy):
    def __init__(self) -> None:
        self._order: OrderedDict[int, None] = OrderedDict()

    def on_insert(self, way_index: int) -> None:
        self._order[way_index] = None
        self._order.move_to_end(way_index)

    def on_access(self, way_index: int) -> None:
        self._order.move_to_end(way_index)

    def select_victim(self) -> int:
        if not self._order:
            raise RuntimeError("Cannot select victim from an empty set")
        return next(iter(self._order))

    def reset(self) -> None:
        self._order.clear()


class FIFOPolicy(ReplacementPolicy):
    def __init__(self) -> None:
        self._order: OrderedDict[int, None] = OrderedDict()

    def on_insert(self, way_index: int) -> None:
        self._order[way_index] = None
        self._order.move_to_end(way_index)

    def on_access(self, way_index: int) -> None:
        pass

    def select_victim(self) -> int:
        if not self._order:
            raise RuntimeError("Cannot select victim from an empty set")
        return next(iter(self._order))

    def reset(self) -> None:
        self._order.clear()


class LFUPolicy(ReplacementPolicy):
    def __init__(self) -> None:
        self._freq: dict[int, int] = {}
        self._last_used: dict[int, int] = {}
        self._tick: int = 0

    def on_insert(self, way_index: int) -> None:
        self._tick += 1
        self._freq[way_index] = 1
        self._last_used[way_index] = self._tick

    def on_access(self, way_index: int) -> None:
        self._tick += 1
        self._freq[way_index] += 1
        self._last_used[way_index] = self._tick

    def select_victim(self) -> int:
        if not self._freq:
            raise RuntimeError("Cannot select victim from an empty set")
        return min(self._freq, key=lambda way: (self._freq[way], self._last_used[way]))

    def reset(self) -> None:
        self._freq.clear()
        self._last_used.clear()
        self._tick = 0


class RandomPolicy(ReplacementPolicy):
    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng if rng is not None else random.Random()
        self._ways: list[int] = []

    def on_insert(self, way_index: int) -> None:
        if way_index not in self._ways:
            self._ways.append(way_index)

    def on_access(self, way_index: int) -> None:
        pass

    def select_victim(self) -> int:
        if not self._ways:
            raise RuntimeError("Cannot select victim from an empty set")
        return self._rng.choice(self._ways)

    def reset(self) -> None:
        self._ways.clear()


def create_replacement_policy(
    policy_type: ReplacementPolicyType, rng: random.Random | None = None
) -> ReplacementPolicy:
    if policy_type == ReplacementPolicyType.LRU:
        return LRUPolicy()
    if policy_type == ReplacementPolicyType.FIFO:
        return FIFOPolicy()
    if policy_type == ReplacementPolicyType.LFU:
        return LFUPolicy()
    if policy_type == ReplacementPolicyType.RANDOM:
        return RandomPolicy(rng=rng)
    raise ValueError(f"Unsupported replacement policy: {policy_type}")
