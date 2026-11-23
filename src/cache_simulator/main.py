import argparse
from pathlib import Path

from cache_simulator.core.cache import Cache
from cache_simulator.core.config import CacheConfig, ReplacementPolicyType
from cache_simulator.core.simulator import Simulator
from cache_simulator.core.trace import MemoryOperation, StepEvent
from cache_simulator.io.trace_parser import load_trace_file, parse_trace_lines

_FALLBACK_TRACE = [
    "R 0x0000",
    "R 0x0004",
    "R 0x0040",
    "R 0x0000",
    "R 0x0020",
    "R 0x0000",
    "W 0x0044",
    "R 0x0080",
    "R 0x00C0",
    "R 0x0008",
]


def _format_details(event: StepEvent) -> str:
    if event.hit:
        return "-"
    if not event.evicted:
        return f"loaded block {event.decoded.block_address:#x}"
    dirty_info = " (DIRTY)" if event.dirty_eviction else ""
    return f"evicted tag {event.evicted_tag:#x}{dirty_info}"


def print_step_by_step(sim: Simulator) -> None:
    cfg = sim.cache.config
    print("=" * 82)
    print(
        f"Architektura: {cfg.mapping_type.value.upper()} | "
        f"Polityka: {cfg.policy.value.upper()} | "
        f"Rozmiar: {cfg.cache_size}B | Blok: {cfg.block_size}B"
    )
    print(
        f"Geometria: zbiory={cfg.num_sets}, linie/zbiór={cfg.associativity} | "
        f"Bity adresu ({cfg.address_bits}b): "
        f"[Tag={cfg.tag_bits} | Index={cfg.index_bits} | Offset={cfg.offset_bits}]"
    )
    print("-" * 82)
    print(
        f"{'Krok':>4} | {'Op':<2} | {'Adres':<6} | {'Tag':<6} | "
        f"{'Idx':>3} | {'Off':<4} | {'Wynik':<5} | {'Miejsce':<7} | Szczegóły"
    )
    print("-" * 82)

    while (event := sim.step()) is not None:
        result = "HIT" if event.hit else "MISS"
        place = f"S{event.set_index}/W{event.way_index}"
        print(
            f"{event.step_number:>4} | "
            f"{event.operation.op_type.value:<2} | "
            f"{event.decoded.raw:#06x} | "
            f"{event.decoded.tag:#06x} | "
            f"{event.decoded.index:>3} | "
            f"{event.decoded.offset:#04x} | "
            f"{result:<5} | "
            f"{place:<7} | "
            f"{_format_details(event)}"
        )

    stats = sim.cache.stats
    print("-" * 82)
    print(
        f"Podsumowanie: dostępy={stats.total_accesses}, "
        f"hits={stats.hits}, misses={stats.misses}, "
        f"evictions={stats.evictions}, hit_rate={stats.hit_rate:.1%}"
    )


def print_cache_contents(cache: Cache) -> None:
    print("\nStan końcowy pamięci cache:")
    for set_idx, cache_set in enumerate(cache.sets):
        ways_str = []
        for way_idx, line in enumerate(cache_set.lines):
            if line.valid:
                dirty_flag = "D" if line.dirty else "-"
                ways_str.append(f"W{way_idx}[V|{dirty_flag}|tag={line.tag:#x}]")
            else:
                ways_str.append(f"W{way_idx}[pusty]")
        print(f"  Set {set_idx:>2}: " + "  ".join(ways_str))


def print_comparison(
    operations: list[MemoryOperation],
    cache_size: int,
    block_size: int,
    address_bits: int,
) -> None:
    num_lines = cache_size // block_size
    variants: list[tuple[str, CacheConfig]] = [
        (
            "Direct-Mapped (1-way)",
            CacheConfig(
                cache_size, block_size, 1, ReplacementPolicyType.LRU, address_bits
            ),
        ),
        (
            "2-Way Set-Assoc (LRU)",
            CacheConfig(
                cache_size, block_size, 2, ReplacementPolicyType.LRU, address_bits
            ),
        ),
        (
            "2-Way Set-Assoc (FIFO)",
            CacheConfig(
                cache_size, block_size, 2, ReplacementPolicyType.FIFO, address_bits
            ),
        ),
        (
            "2-Way Set-Assoc (LFU)",
            CacheConfig(
                cache_size, block_size, 2, ReplacementPolicyType.LFU, address_bits
            ),
        ),
        (
            "2-Way Set-Assoc (Random)",
            CacheConfig(
                cache_size, block_size, 2, ReplacementPolicyType.RANDOM, address_bits
            ),
        ),
        (
            f"Fully Associative ({num_lines}-way LRU)",
            CacheConfig(
                cache_size,
                block_size,
                num_lines,
                ReplacementPolicyType.LRU,
                address_bits,
            ),
        ),
    ]

    print("\n" + "=" * 72)
    print(f"PORÓWNANIE WARIANTÓW (cache={cache_size}B, blok={block_size}B)")
    print("-" * 72)
    print(
        f"{'Wariant architektury':<32} | {'Hits':>5} | {'Miss':>5} | "
        f"{'Evict':>5} | {'Hit Rate':>8}"
    )
    print("-" * 72)

    for label, cfg in variants:
        sim = Simulator(Cache(cfg, seed=42), operations)
        sim.run_all()
        s = sim.cache.stats
        print(
            f"{label:<32} | {s.hits:>5} | {s.misses:>5} | "
            f"{s.evictions:>5} | {s.hit_rate:>7.1%}"
        )
    print("=" * 72)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Symulator wariantów architektury pamięci cache (CLI demo)"
    )
    parser.add_argument("--trace", type=Path, help="Ścieżka do pliku .trace")
    parser.add_argument("--cache-size", type=int, default=64, help="Rozmiar cache [B]")
    parser.add_argument("--block-size", type=int, default=16, help="Rozmiar bloku [B]")
    parser.add_argument(
        "--associativity",
        type=int,
        default=2,
        help="Asocjatywność (1=Direct, N=Set-Assoc)",
    )
    parser.add_argument(
        "--policy",
        type=str,
        default="lru",
        choices=[p.value for p in ReplacementPolicyType],
        help="Polityka zastępowania",
    )
    parser.add_argument("--address-bits", type=int, default=16, help="Szerokość adresu")
    parser.add_argument(
        "--step-by-step",
        action="store_true",
        help="Pokaż dokładny przebieg krok po kroku",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    default_trace = Path("examples/demo.trace")
    if args.trace is not None:
        operations = load_trace_file(args.trace)
        source_label = str(args.trace)
    elif default_trace.exists():
        operations = load_trace_file(default_trace)
        source_label = str(default_trace)
    else:
        operations = parse_trace_lines(_FALLBACK_TRACE)
        source_label = "wbudowany ślad demo"

    print(f"Wczytano {len(operations)} operacji z: {source_label}\n")

    if args.trace is None and not args.step_by_step:
        demo_cfg = CacheConfig(
            cache_size=args.cache_size,
            block_size=args.block_size,
            associativity=2,
            policy=ReplacementPolicyType.LRU,
            address_bits=args.address_bits,
        )
        demo_sim = Simulator(Cache(demo_cfg, seed=42), operations)
        print_step_by_step(demo_sim)
        print_cache_contents(demo_sim.cache)
        print_comparison(
            operations,
            cache_size=args.cache_size,
            block_size=args.block_size,
            address_bits=args.address_bits,
        )
        return

    cfg = CacheConfig(
        cache_size=args.cache_size,
        block_size=args.block_size,
        associativity=args.associativity,
        policy=ReplacementPolicyType(args.policy),
        address_bits=args.address_bits,
    )
    sim = Simulator(Cache(cfg, seed=42), operations)

    if args.step_by_step:
        print_step_by_step(sim)
        print_cache_contents(sim.cache)
    else:
        sim.run_all()
        s = sim.cache.stats
        print(
            f"Wynik ({cfg.mapping_type.value}, {cfg.policy.value}): "
            f"hits={s.hits}, misses={s.misses}, evictions={s.evictions}, "
            f"hit_rate={s.hit_rate:.1%}"
        )
        print_comparison(
            operations,
            cache_size=args.cache_size,
            block_size=args.block_size,
            address_bits=args.address_bits,
        )


if __name__ == "__main__":
    main()
