"""Strict, privacy-preserving structural comparison for JSONL case files."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


class _DuplicateKey(ValueError):
    pass


def _object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey
        result[key] = value
    return result


def _reject_constant(_: str) -> Any:
    raise ValueError("non-finite number")


def _finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError("non-finite number")
    return value


def _equal(left: Any, right: Any) -> bool:
    """Compare JSON values, ignoring object order but preserving array order."""
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_equal(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    # Python considers True == 1; JSON booleans and numbers are distinct types.
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right


def _diagnostic(file: str, line: int, code: str, message: str) -> dict[str, Any]:
    return {"file": file, "line": line, "code": code, "message": message}


def _load(path: Path, label: str) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    rows: dict[str, dict[str, Any]] = {}
    diagnostics: list[dict[str, Any]] = []
    try:
        raw = path.read_bytes()
    except OSError:
        return rows, [_diagnostic(label, 0, "file_read_error", "Unable to read input file.")]

    try:
        content = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        line = raw[: exc.start].count(b"\n") + 1
        return rows, [_diagnostic(label, line, "invalid_utf8", "Input is not valid UTF-8.")]

    # JSONL uses LF record boundaries. Unicode separators are legal inside a
    # JSON string and must not be treated as record delimiters.
    lines = content.split("\n")
    if lines and lines[-1] == "" and content.endswith("\n"):
        lines.pop()
    for line_number, line in enumerate(lines, start=1):
        if line.endswith("\r"):
            line = line[:-1]
        try:
            value = json.loads(
                line,
                object_pairs_hook=_object_from_pairs,
                parse_constant=_reject_constant,
                parse_float=_finite_float,
            )
        except _DuplicateKey:
            diagnostics.append(_diagnostic(label, line_number, "duplicate_key", "Object contains a duplicate key."))
            continue
        except (json.JSONDecodeError, ValueError):
            diagnostics.append(_diagnostic(label, line_number, "malformed_json", "Line is not valid strict JSON."))
            continue

        if not isinstance(value, dict):
            diagnostics.append(_diagnostic(label, line_number, "non_object_row", "Each row must be a JSON object."))
            continue
        case_id = value.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            diagnostics.append(_diagnostic(label, line_number, "invalid_id", "Each row must have a nonempty string id."))
            continue
        if case_id in rows:
            diagnostics.append(_diagnostic(label, line_number, "duplicate_id", "Case IDs must be unique within a file."))
            continue
        rows[case_id] = value

    return rows, diagnostics


def compare_files(base_path: Path, candidate_path: Path) -> dict[str, Any]:
    """Compare two strict JSONL files without exposing case values."""
    base, base_diagnostics = _load(Path(base_path), "base")
    candidate, candidate_diagnostics = _load(Path(candidate_path), "candidate")
    diagnostics = base_diagnostics + candidate_diagnostics
    if diagnostics:
        return {
            "identical": False,
            "base_count": len(base),
            "candidate_count": len(candidate),
            "added": [],
            "removed": [],
            "changed": [],
            "diagnostics": diagnostics,
        }

    base_ids, candidate_ids = set(base), set(candidate)
    added = sorted(candidate_ids - base_ids)
    removed = sorted(base_ids - candidate_ids)
    changed: list[dict[str, Any]] = []
    for case_id in sorted(base_ids & candidate_ids):
        left, right = base[case_id], candidate[case_id]
        fields = sorted(key for key in left.keys() | right.keys() if key not in left or key not in right or not _equal(left[key], right[key]))
        if fields:
            changed.append({"id": case_id, "fields": fields})

    return {
        "identical": not added and not removed and not changed,
        "base_count": len(base),
        "candidate_count": len(candidate),
        "added": added,
        "removed": removed,
        "changed": changed,
        "diagnostics": [],
    }
