from collections.abc import Iterable
from pathlib import Path

from cache_simulator.core.trace import MemoryOperation, OperationType

_OP_MAP: dict[str, OperationType] = {
    "R": OperationType.READ,
    "READ": OperationType.READ,
    "L": OperationType.READ,
    "W": OperationType.WRITE,
    "WRITE": OperationType.WRITE,
    "S": OperationType.WRITE,
}


class TraceParseError(ValueError):
    pass


def parse_trace_lines(lines: Iterable[str]) -> list[MemoryOperation]:
    operations: list[MemoryOperation] = []

    for line_number, raw_line in enumerate(lines, start=1):
        clean_line = raw_line.split("#", maxsplit=1)[0].strip()
        if not clean_line:
            continue

        parts = clean_line.split()
        if len(parts) != 2:
            raise TraceParseError(
                f"Line {line_number}: expected '<OP> <ADDRESS>', got {raw_line.strip()!r}"
            )

        op_token, addr_token = parts
        op_type = _OP_MAP.get(op_token.upper())
        if op_type is None:
            raise TraceParseError(f"Line {line_number}: unknown operation {op_token!r}")

        try:
            address = int(addr_token, 0)
        except ValueError as exc:
            raise TraceParseError(
                f"Line {line_number}: invalid address {addr_token!r}"
            ) from exc

        if address < 0:
            raise TraceParseError(
                f"Line {line_number}: address cannot be negative ({address})"
            )

        operations.append(MemoryOperation(op_type=op_type, address=address))

    return operations


def load_trace_file(path: str | Path) -> list[MemoryOperation]:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as file:
        return parse_trace_lines(file)
