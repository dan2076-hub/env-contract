"""Command line interface with safe diagnostics."""
import argparse
import json
from pathlib import Path
import sys

from .core import Comparison, Document, compare_documents, parse_document


def read_document(path: Path, role: str) -> tuple[Document, list[dict[str, str]]]:
    try:
        return parse_document(path.read_text(encoding='utf-8-sig')), []
    except UnicodeError:
        return Document(), [{'file': role, 'kind': 'invalid_encoding'}]
    except OSError:
        return Document(), [{'file': role, 'kind': 'unreadable'}]


def format_text(result: Comparison, strict: bool = False) -> str:
    lines = []
    unexpected_label = 'Unexpected (failure)' if strict else 'Unexpected (warning)'
    for label, keys in [('Missing', result.missing), ('Empty', result.empty), (unexpected_label, result.unexpected)]:
        if keys:
            lines.append(label + ': ' + ', '.join(keys))
    for role, duplicates in result.duplicates.items():
        for key, numbers in duplicates.items():
            lines.append(f'Duplicate ({role}): {key}; lines ' + ', '.join(map(str, numbers)))
    for role, numbers in result.invalid_lines.items():
        if numbers:
            lines.append(f'Invalid syntax ({role}); lines ' + ', '.join(map(str, numbers)))
    for error in result.errors:
        lines.append(f"File error ({error['file']}): {error['kind']}")
    lines.append('Contract OK' if result.exit_code(strict) == 0 else 'Contract failed')
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Check .env keys against an example without displaying values.')
    parser.add_argument('actual', type=Path, help='Actual environment file')
    parser.add_argument('--example', type=Path, default=Path('.env.example'), help='Example contract (default: .env.example)')
    parser.add_argument('--json', action='store_true', help='Print one machine-readable JSON report')
    parser.add_argument('--strict', action='store_true', help='Fail on unexpected keys as well')
    args = parser.parse_args(argv)
    actual, actual_errors = read_document(args.actual, 'actual')
    example, example_errors = read_document(args.example, 'example')
    result = compare_documents(actual, example)
    result.errors.extend(actual_errors + example_errors)
    print(json.dumps(result.to_dict(args.strict), ensure_ascii=False) if args.json else format_text(result, args.strict))
    return result.exit_code(args.strict)
