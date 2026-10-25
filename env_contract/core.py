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

    def exit_code(self, strict: bool = False) -> int:
        if self.errors or any(self.invalid_lines.values()):
            return 2
        if self.missing or self.empty or any(self.duplicates.values()) or (strict and self.unexpected):
            return 1
        return 0

    def to_dict(self, strict: bool = False) -> dict:
        return {
            'schema_version': 1, 'missing': self.missing, 'empty': self.empty,
            'unexpected': self.unexpected, 'duplicates': self.duplicates,
            'invalid_lines': self.invalid_lines, 'errors': self.errors,
            'ok': self.exit_code(strict) == 0,
        }


def value_is_empty(raw: str) -> bool | None:
    """Return emptiness, or None for invalid syntax, without retaining a value."""
    stripped = raw.lstrip()
    if not stripped or stripped[0] not in {'"', "'"}:
        return not re.sub(r'\s+#.*$', '', raw).strip()
    quote = stripped[0]
    index = 1
    while index < len(stripped):
        character = stripped[index]
        if quote == '"' and character == '\\':
            index += 2
            continue
        if character == quote:
            tail = stripped[index + 1:].strip()
            if tail and not tail.startswith('#'):
                return None
            return not stripped[1:index].strip()
        index += 1
    return None


def parse_document(text: str) -> Document:
    entries: dict[str, list[Occurrence]] = {}
    invalid = []
    for line_number, line in enumerate(text.removeprefix('\ufeff').splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = ASSIGNMENT.fullmatch(line)
        if not match:
            invalid.append(line_number)
            continue
        empty = value_is_empty(match[2])
        if empty is None:
            invalid.append(line_number)
            continue
        entries.setdefault(match[1], []).append(Occurrence(line_number, empty))
    return Document({key: tuple(items) for key, items in sorted(entries.items())}, tuple(invalid))


def compare_documents(actual: Document, example: Document) -> Comparison:
    actual_keys, expected_keys = set(actual.entries), set(example.entries)
    return Comparison(
        missing=sorted(expected_keys - actual_keys),
        empty=sorted(key for key in actual_keys & expected_keys if any(item.empty for item in actual.entries[key])),
        unexpected=sorted(actual_keys - expected_keys),
        duplicates={role: {key: [item.line for item in items] for key, items in document.entries.items() if len(items) > 1}
                    for role, document in [('actual', actual), ('example', example)]},
        invalid_lines={'actual': list(actual.invalid_lines), 'example': list(example.invalid_lines)},
    )
