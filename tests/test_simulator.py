import pytest

from cache_simulator.core.cache import Cache
from cache_simulator.core.config import CacheConfig
from cache_simulator.core.simulator import Simulator
from cache_simulator.io.trace_parser import parse_trace_lines


def test_simulator_step_run_and_reset() -> None:
    ops = parse_trace_lines(
        [
            "R 0x0000",
            "R 0x0004",
            "R 0x0040",
            "R 0x0000",
        ]
    )
    cfg = CacheConfig(cache_size=64, block_size=16, associativity=1, address_bits=16)
    sim = Simulator(Cache(cfg), ops)

    assert sim.current_step == 0
    assert sim.total_steps == 4
    assert sim.is_finished is False

    first = sim.step()
    assert first is not None
    assert first.step_number == 1
    assert first.hit is False
    assert sim.current_step == 1

    rest = sim.run_all()
    assert len(rest) == 3
    assert sim.is_finished is True
    assert sim.step() is None
    assert len(sim.history) == 4
    assert sim.cache.stats.hits == 1

    # Reset pozwala puścić ten sam ślad od nowa
    sim.reset()
    assert sim.current_step == 0
    assert sim.is_finished is False
    assert len(sim.history) == 0
    assert sim.cache.stats.total_accesses == 0


def test_compare_two_architectures_on_same_trace() -> None:
    ops = parse_trace_lines(
        [
            "R 0x0000",
            "R 0x0040",
            "R 0x0000",
            "R 0x0040",
        ]
    )

    dm_sim = Simulator(
        Cache(
            CacheConfig(cache_size=64, block_size=16, associativity=1, address_bits=16)
        ),
        ops,
    )
    sa_sim = Simulator(
        Cache(
            CacheConfig(cache_size=64, block_size=16, associativity=2, address_bits=16)
        ),
        ops,
    )

    dm_sim.run_all()
    sa_sim.run_all()

    assert dm_sim.cache.stats.hit_rate == pytest.approx(0.0)
    assert sa_sim.cache.stats.hit_rate == pytest.approx(0.5)
