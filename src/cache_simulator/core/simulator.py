from collections.abc import Sequence

from cache_simulator.core.cache import Cache
from cache_simulator.core.trace import MemoryOperation, StepEvent


class Simulator:
    def __init__(
        self,
        cache: Cache,
        operations: Sequence[MemoryOperation] = (),
    ) -> None:
        self._cache = cache
        self._operations: tuple[MemoryOperation, ...] = tuple(operations)
        self._cursor: int = 0
        self._history: list[StepEvent] = []

    @property
    def cache(self) -> Cache:
        return self._cache

    @property
    def operations(self) -> tuple[MemoryOperation, ...]:
        return self._operations

    @property
    def current_step(self) -> int:
        return self._cursor

    @property
    def total_steps(self) -> int:
        return len(self._operations)

    @property
    def is_finished(self) -> bool:
        return self._cursor >= len(self._operations)

    @property
    def history(self) -> tuple[StepEvent, ...]:
        return tuple(self._history)

    def load_operations(self, operations: Sequence[MemoryOperation]) -> None:
        self._operations = tuple(operations)
        self.reset()

    def step(self) -> StepEvent | None:
        if self.is_finished:
            return None

        operation = self._operations[self._cursor]
        event = self._cache.access(operation)
        self._cursor += 1
        self._history.append(event)
        return event

    def run_steps(self, count: int) -> list[StepEvent]:
        if count < 0:
            raise ValueError("count must be non-negative")

        events: list[StepEvent] = []
        for _ in range(count):
            event = self.step()
            if event is None:
                break
            events.append(event)
        return events

    def run_all(self) -> list[StepEvent]:
        events: list[StepEvent] = []
        while (event := self.step()) is not None:
            events.append(event)
        return events

    def reset(self) -> None:
        self._cache.reset()
        self._cursor = 0
        self._history.clear()
