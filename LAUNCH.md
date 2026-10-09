# Launch notes

`evalcase-diff` is ready for a local, offline launch from a clean checkout.

## Run it

Install the package and compare two files:

```console
python -m pip install .
evalcase-diff compare BASE.jsonl CANDIDATE.jsonl
```

Use `--format json` for stable machine-readable output, or run directly from a
checkout with `python -m evalcase_diff compare BASE.jsonl CANDIDATE.jsonl`.

## Read the result

- Exit `0`: the files contain the same cases and values.
- Exit `1`: both files are valid and at least one case was added, removed, or
  changed.
- Exit `2`: input is invalid or cannot be read.

The report includes case counts, sorted case IDs, and sorted changed top-level
field names. It does not include row values or parser exception text. Invalid
input diagnostics identify the side, line, and safe diagnostic summary.

## Scope

The program reads local strict JSONL and uses only the Python standard library
at runtime. It does not contact providers, run evaluations, call models, or
claim that a dataset or model is better. The checked-in examples are synthetic.
