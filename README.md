# EvalCase Diff

Review how local AI evaluation cases changed before running another provider-backed evaluation. `evalcase-diff` compares strict JSONL files by stable `id` and reports added, removed, and changed cases. It never prints case values.

## Quickstart

Requires Python 3.10 or newer. From a fresh checkout:

```console
python -m pip install .
evalcase-diff compare examples/identical.jsonl examples/identical.jsonl --format text
```

The identical-file example exits 0 and reports no differences. To inspect a synthetic change:

```console
evalcase-diff compare examples/base.jsonl examples/candidate.jsonl --format text
```

Valid differences exit 1; invalid input exits 2. JSON output is available with `--format json`.

For an editable checkout without installing the command, run
`python -m evalcase_diff compare BASE.jsonl CANDIDATE.jsonl` from the repository
root. Text output lists sorted IDs and changed top-level field names. JSON output
uses the same stable result fields: `identical`, `base_count`,
`candidate_count`, `added`, `removed`, `changed`, and `diagnostics`.

## Input contract

Each JSONL row must be an object with a nonempty string `id`. Other JSON fields are allowed and compared structurally. Duplicate IDs/keys, malformed or non-finite JSON, invalid UTF-8, and invalid rows are rejected. Object key order does not matter; array order does. Changed rows report only top-level field names, never values.

The tool is offline and uses Python's standard library at runtime. It does not call models, providers, networks, or evaluation systems and makes no quality or benchmark claim. Public examples use synthetic data only.
