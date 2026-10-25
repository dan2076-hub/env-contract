# env-contract

Catch missing environment keys before running an application, without displaying configuration values.

Requires Python 3.11 or newer. No runtime dependencies.

```sh
python -m env_contract examples/sample.env --example examples/sample.env.example
# Contract OK
```

Install from a checkout with `python -m pip install .`, then use `env-contract` with the same arguments.

The actual file is required; the example defaults to `.env.example`. Missing keys fail the check. Additional keys are warnings. Blank lines, comments, an optional `export` prefix, and one-line `KEY=value` assignments are recognized. This initial version compares keys; detailed value syntax and emptiness checks are being added separately.

Output contains key names and line numbers, never values. The tool does not modify inputs or access the network.

Exit codes: `0` accepted, `1` contract failed, `2` file or syntax error.

## Development

```sh
python -m unittest discover -s tests -v
```

MIT licensed; see [LICENSE](LICENSE).
