# env-contract

Catch missing environment keys before running an application, without displaying configuration values.

Requires Python 3.11 or newer. No runtime dependencies.

[Русский](README.ru.md)

```sh
python -m env_contract examples/sample.env --example examples/sample.env.example
# Contract OK
```

Install from a checkout with `python -m pip install .`, then use `env-contract` with the same arguments.

To get the source:

```sh
git clone https://github.com/dan2076-hub/env-contract.git
cd env-contract
python -m pip install .
env-contract examples/sample.env --example examples/sample.env.example --json
```

The actual file is required; the example defaults to `.env.example`. Missing or empty expected keys fail the check. Additional keys are warnings. Duplicate keys in either file fail, with all occurrence line numbers.

## Supported syntax

- UTF-8 with an optional BOM; LF and CRLF line endings.
- Blank lines, full-line comments, optional `export`, and keys matching `[A-Za-z_][A-Za-z0-9_]*`.
- One-line unquoted, single-quoted and double-quoted values. In double quotes, an escaped character is skipped when locating the closing quote; single quotes close at the next single quote.
- After a closing quote, only whitespace and an optional comment are accepted.
- An unquoted `#` starts a comment only after whitespace: `KEY=#literal` is nonempty; `KEY= # comment` is empty.
- Quoted or unquoted whitespace counts as empty. Any empty occurrence of an expected key is reported. Empty example values still require a nonempty actual value.

Variables, shell expressions and escape sequences are never evaluated or expanded. Multiline quoted values and malformed assignments are rejected, with line numbers only. This is a deliberately small contract checker, not a full shell or dotenv implementation.

Output contains key names and line numbers, never values. The tool does not modify inputs or access the network.

## Automation and exit codes

```sh
env-contract .env --example .env.example --strict --json
```

`--strict` makes unexpected keys failures. `--json` emits a single JSON object, including handled file, decoding and syntax errors. Invalid CLI arguments use argparse diagnostics on stderr.

```json
{"schema_version": 1, "missing": ["API_KEY"], "empty": [], "unexpected": [], "duplicates": {"actual": {}, "example": {}}, "invalid_lines": {"actual": [], "example": []}, "errors": [], "ok": false}
```

| Exit | Meaning |
| --- | --- |
| `0` | Contract accepted; unexpected keys may be warnings |
| `1` | Missing/empty expected keys, duplicates, or strict unexpected keys |
| `2` | Invalid arguments, unreadable files, invalid UTF-8 or malformed assignments |

Syntax and file errors take precedence over validation failures. File errors contain only a role (`actual`/`example`) and a safe kind (`unreadable`/`invalid_encoding`). If either file has invalid syntax, key metadata from the malformed file is discarded and all key comparisons are suppressed: assignment-like text after an unclosed quote may be secret content. Only invalid line numbers are reported. After I/O failures, any displayed differences are provisional and `ok` is false. Names and lists are sorted; line numbers start at 1. JSON schema version is 1.

This checks key contracts; it does not validate URLs or types, find leaked credentials, generate files, or offer autofixes. Configuration is read into process memory for parsing, but values are not retained in result objects or printed.

## Development

```sh
python -m unittest discover -s tests -v
python -m pip wheel --no-deps . --wheel-dir dist
```

GitHub Actions runs the suite and installed CLI on Windows/Linux with Python 3.11 and 3.13. Tests include synthetic secret sentinels, quoting, BOM/CRLF and JSON failure reports.

MIT licensed; see [LICENSE](LICENSE).
