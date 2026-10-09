import json

from evalcase_diff.engine import compare_files


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, allow_nan=True) + "\n" for row in rows), encoding="utf-8")


def test_identical_files_have_empty_change_sets(tmp_path):
    left = tmp_path / "left.jsonl"
    right = tmp_path / "right.jsonl"
    write_jsonl(left, [{"id": "b", "value": 2}, {"id": "a", "value": 1}])
    write_jsonl(right, [{"id": "b", "value": 2}, {"id": "a", "value": 1}])

    result = compare_files(left, right)

    assert result["identical"] is True
    assert result["base_count"] == result["candidate_count"] == 2
    assert result["added"] == result["removed"] == result["changed"] == []
    assert result["diagnostics"] == []


def test_additions_removals_and_changes_are_sorted_and_values_are_not_echoed(tmp_path):
    base = tmp_path / "base.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    secret = "SYNTHETIC_SECRET_MUST_NOT_APPEAR"
    write_jsonl(base, [{"id": "z-remove", "old": secret}, {"id": "b-change", "value": 1}, {"id": "a-remove"}])
    write_jsonl(candidate, [{"id": "y-add", "new": secret}, {"id": "b-change", "value": 2}, {"id": "x-add"}])

    result = compare_files(base, candidate)

    assert result["identical"] is False
    assert result["added"] == ["x-add", "y-add"]
    assert result["removed"] == ["a-remove", "z-remove"]
    assert result["changed"] == [{"id": "b-change", "fields": ["value"]}]
    assert secret not in json.dumps(result)


def test_changed_reports_only_sorted_top_level_field_names(tmp_path):
    base, candidate = tmp_path / "base.jsonl", tmp_path / "candidate.jsonl"
    write_jsonl(base, [{"id": "c", "zeta": 1, "alpha": 2, "same": 3}])
    write_jsonl(candidate, [{"id": "c", "zeta": 9, "alpha": 8, "same": 3}])

    assert compare_files(base, candidate)["changed"] == [
        {"id": "c", "fields": ["alpha", "zeta"]}
    ]


def test_object_key_order_is_irrelevant_but_array_order_matters(tmp_path):
    base, candidate = tmp_path / "base.jsonl", tmp_path / "candidate.jsonl"
    write_jsonl(base, [{"id": "object", "value": {"a": 1, "b": 2}}, {"id": "array", "value": [1, 2]}])
    write_jsonl(candidate, [{"id": "object", "value": {"b": 2, "a": 1}}, {"id": "array", "value": [2, 1]}])

    result = compare_files(base, candidate)

    assert result["changed"] == [{"id": "array", "fields": ["value"]}]


def test_invalid_inputs_return_diagnostics_without_values(tmp_path):
    cases = {
        "duplicate-id": '{"id":"dup"}\n{"id":"dup"}\n',
        "duplicate-key": '{"id":"one","x":1,"x":2}\n',
        "nan": '{"id":"one","x":NaN}\n',
        "infinity": '{"id":"one","x":Infinity}\n',
        "malformed": '{"id":"one"\n',
        "bad-id": '{"id":7}\n',
        "blank-id": '{"id":"   "}\n',
        "missing-id": '{"value":"SYNTHETIC_SECRET_MUST_NOT_APPEAR"}\n',
        "non-object": '[1,2,3]\n',
        "blank-line": '\n',
    }
    secret = "SYNTHETIC_SECRET_MUST_NOT_APPEAR"
    for name, content in cases.items():
        base, candidate = tmp_path / f"{name}.jsonl", tmp_path / f"{name}-candidate.jsonl"
        base.write_text(content, encoding="utf-8")
        candidate.write_text('{"id":"valid"}\n', encoding="utf-8")
        result = compare_files(base, candidate)
        assert result["identical"] is False
        assert result["diagnostics"], name
        assert all({"file", "line", "code", "message"} <= item.keys() for item in result["diagnostics"])
        assert secret not in json.dumps(result)


def test_invalid_utf8_is_reported_as_diagnostic(tmp_path):
    base, candidate = tmp_path / "invalid.jsonl", tmp_path / "valid.jsonl"
    base.write_bytes(b'{"id":"\xff"}\n')
    candidate.write_text('{"id":"ok"}\n', encoding="utf-8")

    result = compare_files(base, candidate)

    assert result["diagnostics"]
    assert all({"file", "line", "code", "message"} <= item.keys() for item in result["diagnostics"])


def test_examples_are_synthetic_and_show_no_change_and_change(tmp_path):
    from pathlib import Path

    examples = Path(__file__).resolve().parents[1] / "examples"
    same = compare_files(examples / "identical.jsonl", examples / "identical.jsonl")
    changed = compare_files(examples / "base.jsonl", examples / "candidate.jsonl")

    assert same["identical"] is True
    assert changed["added"] == ["case-003"]
    assert changed["removed"] == ["case-002"]


def test_unicode_line_separator_inside_json_string_is_not_a_record_boundary(tmp_path):
    base = tmp_path / "base.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    row = '{"id":"case-1","text":"left\u2028right"}\n'
    base.write_text(row, encoding="utf-8")
    candidate.write_text(row, encoding="utf-8")

    result = compare_files(base, candidate)

    assert result["identical"] is True
    assert result["base_count"] == result["candidate_count"] == 1


def test_numeric_overflow_that_decodes_as_infinity_is_rejected(tmp_path):
    base = tmp_path / "base.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    base.write_text('{"id":"safe","value":1e999}\n', encoding="utf-8")
    candidate.write_text('{"id":"safe","value":1}\n', encoding="utf-8")

    result = compare_files(base, candidate)

    assert result["identical"] is False
    assert result["diagnostics"][0]["code"] == "malformed_json"
    assert "1e999" not in json.dumps(result)
