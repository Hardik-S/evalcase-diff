# Independent v0.1.0 release review

**Result: PASS**

Reviewed commit `6d335aaa600c244453ee918df8f3ce0b30494f66` (`feat/evalcase-diff-v0.1.0`) against issue #5's frozen contract. The checkout was clean before review. No contract blocker was reproduced; no repair is required.

## Commands and results

- `git rev-parse HEAD` -> `6d335aaa600c244453ee918df8f3ce0b30494f66`.
- `python -m pytest` -> **12 passed in 0.22s** (Python 3.13.1, pytest 8.4.2).
- Fresh install: `python -m venv $venvPath` followed by `& (Join-Path $venvPath 'Scripts\python.exe') -m pip install .` -> wheel built and `evalcase-diff-0.1.0` installed successfully in a new temp venv.
- Installed quickstart: `evalcase-diff compare examples/identical.jsonl examples/identical.jsonl --format text` -> exit **0**, `No differences.`; `evalcase-diff compare examples/base.jsonl examples/candidate.jsonl --format text` -> exit **1**, added `case-003`, removed `case-002`.
- Installed adversarial CLI invocations used `evalcase-diff compare BASE CANDIDATE --format json`. Duplicate key -> exit **2**, `duplicate_key`; duplicate ID -> **2**, `duplicate_id`; `NaN` and `Infinity` -> **2**, `malformed_json`; exponent overflow `1e999` -> **2**, `malformed_json`; malformed JSON -> **2**, `malformed_json`; invalid UTF-8 -> **2**, `invalid_utf8`; non-object row -> **2**, `non_object_row`; missing ID -> **2**, `invalid_id`. All diagnostics were value-free.
- Structural comparison probe: same object with reversed key order and array `[1,2]` versus `[2,1]` -> exit **1**, only `array:value` reported changed. This confirms object order is ignored and array order is significant.
- Deterministic ordering probe -> exit **1**, added IDs `b,y`, removed IDs `a,z`, changed entry `c:v` (sorted IDs and field names).
- Privacy probe with distinct synthetic secrets in a changed field -> exit **1**; JSON output contained the changed field name `answer` and neither secret value.
- Exit semantics: identical quickstart **0**, valid differences **1**, invalid inputs **2**.

The malformed, duplicate, non-finite, invalid-row, structural, deterministic-output, privacy, and CLI checks also passed in the committed test suite. I made no changes outside this report and did not commit or push.
