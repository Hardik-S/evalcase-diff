"""Command-line interface for the offline EvalCase Diff tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .engine import compare_files


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evalcase-diff",
        description="Compare two local JSONL evaluation-case files without showing case values.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    compare = subparsers.add_parser("compare", help="compare a base and candidate JSONL file")
    compare.add_argument("base", type=Path, metavar="BASE.jsonl")
    compare.add_argument("candidate", type=Path, metavar="CANDIDATE.jsonl")
    compare.add_argument(
        "--format", choices=("text", "json"), default="text", dest="output_format"
    )
    return parser


def _stable_result(result: dict[str, Any]) -> dict[str, Any]:
    """Copy and order the public result fields without exposing case contents."""
    changed = [
        {"id": item["id"], "fields": sorted(item["fields"])}
        for item in result["changed"]
    ]
    changed.sort(key=lambda item: item["id"])
    diagnostics = [
        {
            "file": item["file"],
            "line": item["line"],
            "code": item["code"],
            "message": item["message"],
        }
        for item in result["diagnostics"]
    ]
    diagnostics.sort(key=lambda item: (str(item["file"]), item["line"], item["code"]))
    return {
        "identical": bool(result["identical"]),
        "base_count": result["base_count"],
        "candidate_count": result["candidate_count"],
        "added": sorted(result["added"]),
        "removed": sorted(result["removed"]),
        "changed": changed,
        "diagnostics": diagnostics,
    }


def _render_text(result: dict[str, Any]) -> str:
    lines = [
        f"Base cases: {result['base_count']}",
        f"Candidate cases: {result['candidate_count']}",
    ]
    if result["diagnostics"]:
        lines.append("Invalid input:")
        for diagnostic in result["diagnostics"]:
            # Diagnostic messages are engine-owned, sanitized summaries. Never
            # render exception text or input row contents in this layer.
            lines.append(
                f"  {diagnostic['file']}:{diagnostic['line']}: "
                f"{diagnostic['code']}: {diagnostic['message']}"
            )
        return "\n".join(lines)

    if result["identical"]:
        lines.append("No differences.")
    else:
        lines.append(f"Added ({len(result['added'])}):")
        lines.extend(f"  {case_id}" for case_id in result["added"])
        lines.append(f"Removed ({len(result['removed'])}):")
        lines.extend(f"  {case_id}" for case_id in result["removed"])
        lines.append(f"Changed ({len(result['changed'])}):")
        lines.extend(
            f"  {item['id']}: {', '.join(item['fields'])}"
            for item in result["changed"]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command != "compare":  # pragma: no cover - argparse requires a subcommand
        return 2
    try:
        result = _stable_result(compare_files(args.base, args.candidate))
    except Exception:
        # Keep filesystem/parser exception text (which can contain input data)
        # out of the terminal. The engine normally returns structured diagnostics.
        print("Invalid input.", file=sys.stderr)
        return 2

    if result["diagnostics"]:
        code = 2
    else:
        code = 0 if result["identical"] else 1
    if args.output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_render_text(result))
    return code
