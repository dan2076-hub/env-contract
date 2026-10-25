"""Environment metadata and comparison; values never leave the parser."""
from dataclasses import dataclass, field
import re

ASSIGNMENT = re.compile(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$')


@dataclass(frozen=True)
class Occurrence:
    line: int
    empty: bool = False


@dataclass(frozen=True)
class Document:
    entries: dict[str, tuple[Occurrence, ...]] = field(default_factory=dict)
    invalid_lines: tuple[int, ...] = ()


@dataclass
class Comparison:
    missing: list[str]
    empty: list[str]
    unexpected: list[str]
    duplicates: dict[str, dict[str, list[int]]]
    invalid_lines: dict[str, list[int]]
    errors: list[dict[str, str]] = field(default_factory=list)

    def exit_code(self) -> int:
        if self.errors or any(self.invalid_lines.values()):
            return 2
        if self.missing or self.empty or any(self.duplicates.values()):
            return 1
        return 0


def parse_document(text: str) -> Document:
    entries: dict[str, list[Occurrence]] = {}
    invalid = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = ASSIGNMENT.fullmatch(line)
        if not match:
            invalid.append(line_number)
            continue
        entries.setdefault(match[1], []).append(Occurrence(line_number))
    return Document({key: tuple(items) for key, items in sorted(entries.items())}, tuple(invalid))


def compare_documents(actual: Document, example: Document) -> Comparison:
    actual_keys, expected_keys = set(actual.entries), set(example.entries)
    return Comparison(
        missing=sorted(expected_keys - actual_keys), empty=[],
        unexpected=sorted(actual_keys - expected_keys),
        duplicates={'actual': {}, 'example': {}},
        invalid_lines={'actual': list(actual.invalid_lines), 'example': list(example.invalid_lines)},
    )
