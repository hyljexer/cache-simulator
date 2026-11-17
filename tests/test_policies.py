import random

import pytest

from cache_simulator.core.config import ReplacementPolicyType
from cache_simulator.core.policies import (
    FIFOPolicy,
    LFUPolicy,
    LRUPolicy,
    RandomPolicy,
    create_replacement_policy,
)


def test_lru_moves_accessed_way_to_most_recent() -> None:
    policy = LRUPolicy()
    policy.on_insert(0)
    policy.on_insert(1)
    policy.on_insert(2)

    # Odwołanie do linii 0 sprawia, że to linia 1 staje się najdawniej używana
    policy.on_access(0)

    assert policy.select_victim() == 1

    # Zastępujemy linię 1 nowym blokiem -> najstarsza staje się linia 2
    policy.on_insert(1)
    assert policy.select_victim() == 2


def test_fifo_ignores_hits_and_evicts_oldest_inserted() -> None:
    policy = FIFOPolicy()
    policy.on_insert(0)
    policy.on_insert(1)
    policy.on_insert(2)

    # W przeciwieństwie do LRU, trafienie w 0 nie chroni jej przed wyrzuceniem
    policy.on_access(0)

    assert policy.select_victim() == 0

    # Po wstawieniu nowego bloku w miejsce 0, najstarsza w kolejce jest 1
    policy.on_insert(0)
    assert policy.select_victim() == 1


def test_lfu_evicts_least_frequent_and_breaks_ties_by_lru() -> None:
    policy = LFUPolicy()
    policy.on_insert(0)  # freq=1, tick=1
    policy.on_insert(1)  # freq=1, tick=2
    policy.on_insert(2)  # freq=1, tick=3

    policy.on_access(0)  # freq=2, tick=4
    policy.on_access(2)  # freq=2, tick=5

    # Linia 1 ma najmniejszą częstość (1)
    assert policy.select_victim() == 1

    # Po podmianie linii 1 jej licznik resetuje się do 1 (a tick=6)
    policy.on_insert(1)
    policy.on_access(1)  # freq=2, tick=6

    # Teraz wszystkie mają freq=2 -> wygrywa remis LRU: linia 0 (tick=4)
    assert policy.select_victim() == 0


def test_random_policy_is_deterministic_with_seed() -> None:
    p1 = RandomPolicy(rng=random.Random(42))
    p2 = RandomPolicy(rng=random.Random(42))

    for way in range(4):
        p1.on_insert(way)
        p2.on_insert(way)

    assert p1.select_victim() == p2.select_victim()
    assert p1.select_victim() in {0, 1, 2, 3}


def test_select_victim_on_empty_policy_raises_error() -> None:
    for policy_type in ReplacementPolicyType:
        policy = create_replacement_policy(policy_type)
        with pytest.raises(RuntimeError, match="empty set"):
            policy.select_victim()
