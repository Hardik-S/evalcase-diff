import json

from evalcase_diff.cli import main


def test_cli_exit_codes_for_identical_diff_and_invalid_input(tmp_path, capsys):
    base = tmp_path / "base.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    base.write_text('{"id":"same"}\n', encoding="utf-8")
    candidate.write_text('{"id":"same"}\n', encoding="utf-8")

    assert main(["compare", str(base), str(candidate)]) == 0
    assert "No differences." in capsys.readouterr().out

    candidate.write_text('{"id":"added"}\n', encoding="utf-8")
    assert main(["compare", str(base), str(candidate)]) == 1
    assert "Added (1):" in capsys.readouterr().out

    candidate.write_text('{"id":"bad","value":NaN}\n', encoding="utf-8")
    assert main(["compare", str(base), str(candidate)]) == 2
    assert "malformed_json" in capsys.readouterr().out


def test_cli_json_format_is_structured_and_does_not_echo_values(tmp_path, capsys):
    base = tmp_path / "base.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    secret = "SYNTHETIC_SECRET_MUST_NOT_APPEAR"
    base.write_text(json.dumps({"id": "same", "value": secret}) + "\n", encoding="utf-8")
    candidate.write_text(json.dumps({"id": "same", "value": "different"}) + "\n", encoding="utf-8")

    assert main(["compare", str(base), str(candidate), "--format", "json"]) == 1
    output = capsys.readouterr().out
    parsed = json.loads(output)
    assert parsed["changed"] == [{"id": "same", "fields": ["value"]}]
    assert secret not in output


def test_cli_missing_file_exits_two_without_exception_details(tmp_path, capsys):
    missing = tmp_path / "does-not-exist.jsonl"
    valid = tmp_path / "valid.jsonl"
    valid.write_text('{"id":"safe"}\n', encoding="utf-8")

    assert main(["compare", str(missing), str(valid)]) == 2
    output = capsys.readouterr().out
    assert "file_read_error" in output
    assert "Traceback" not in output
