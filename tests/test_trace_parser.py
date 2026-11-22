from pathlib import Path

import pytest

from cache_simulator.core.trace import MemoryOperation, OperationType
from cache_simulator.io.trace_parser import (
    TraceParseError,
    load_trace_file,
    parse_trace_lines,
)


def test_parse_trace_lines_handles_comments_and_formats() -> None:
    lines = [
        "# Komentarz na całą linię",
        "   ",
        "R 0x0000",
        "w 0x0040   # zapis pod 0x0040",
        "READ 64",
        "S 0x0080",
        "l 0x0004",
    ]

    ops = parse_trace_lines(lines)

    assert ops == [
        MemoryOperation(OperationType.READ, 0x0000),
        MemoryOperation(OperationType.WRITE, 0x0040),
        MemoryOperation(OperationType.READ, 64),
        MemoryOperation(OperationType.WRITE, 0x0080),
        MemoryOperation(OperationType.READ, 0x0004),
    ]


@pytest.mark.parametrize(
    ("bad_line", "expected_msg"),
    [
        ("R", "expected '<OP> <ADDRESS>'"),
        ("R 0x10 extra", "expected '<OP> <ADDRESS>'"),
        ("X 0x10", "unknown operation"),
        ("R 0xZZZ", "invalid address"),
        ("W -16", "cannot be negative"),
    ],
)
def test_parse_trace_lines_raises_on_invalid_input(
    bad_line: str, expected_msg: str
) -> None:
    with pytest.raises(TraceParseError, match=expected_msg):
        parse_trace_lines(["# ok line", bad_line])


def test_load_trace_file(tmp_path: Path) -> None:
    trace_file = tmp_path / "sample.trace"
    trace_file.write_text("R 0x0010\nW 0x0020\n", encoding="utf-8")

    ops = load_trace_file(trace_file)

    assert len(ops) == 2
    assert ops[0] == MemoryOperation(OperationType.READ, 0x0010)
    assert ops[1] == MemoryOperation(OperationType.WRITE, 0x0020)
