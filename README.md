# env-contract

Catch missing environment keys before running an application, without displaying configuration values.

Requires Python 3.11 or newer. No runtime dependencies.

```sh
python -m env_contract examples/sample.env --example examples/sample.env.example
# Contract OK
```

Install from a checkout with `python -m pip install .`, then use `env-contract` with the same arguments.

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

Exit codes: `0` accepted, `1` contract failed, `2` file or syntax error.

## Development

```sh
python -m unittest discover -s tests -v
```

MIT licensed; see [LICENSE](LICENSE).
