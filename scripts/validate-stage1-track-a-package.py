#!/usr/bin/env python3
"""Validate literal RFP §7–§8 completeness of a Track A package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_ARTIFACTS = {
    "qa-results": ".jsonl",
    "reasoning-traces": ".json",
    "metrics-self-report": ".md",
    "operations-report": ".md",
    "methodology-summary": ".md",
    "clarification-log": ".md",
    "submission-manifest": ".json",
}


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--no-write-report", action="store_true")
    args = parser.parse_args()
    directory = args.directory.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    manifests = list(directory.glob("vendor_*_stage1_submission-manifest_v*.json"))
    if len(manifests) != 1:
        errors.append("expected exactly one versioned submission manifest")
        package = {}
        vendor = ""
        version = 0
    else:
        package = _json(manifests[0])
        vendor = str(package.get("vendor_id") or "")
        version = int(package.get("version") or 0)
    if package.get("stage") != 1 or package.get("track") != "A":
        errors.append("submission manifest must declare Stage 1 Track A")
    if package.get("authoritative") is not True:
        errors.append("submission manifest must identify this version as authoritative")

    prefix = f"vendor_{vendor}_stage1_"
    suffix = f"_v{version}"
    paths: dict[str, Path] = {}
    for artifact, extension in REQUIRED_ARTIFACTS.items():
        expected = directory / f"{prefix}{artifact}{suffix}{extension}"
        if not expected.is_file():
            errors.append(f"missing RFP artifact: {expected.name}")
        else:
            paths[artifact] = expected
            raw = expected.read_bytes()
            if raw.startswith(b"\xef\xbb\xbf"):
                errors.append(f"{expected.name}: UTF-8 BOM is not allowed")
            if raw and not raw.endswith(b"\n"):
                errors.append(f"{expected.name}: missing Unix terminal newline")
            if b"\r\n" in raw:
                errors.append(f"{expected.name}: contains non-Unix line endings")

    if list(directory.glob("*graph-nodes*")) or list(directory.glob("*graph-edges*")):
        errors.append("Track A must not submit a constructed graph")

    validation_path = directory / "validation-report.json"
    if not validation_path.is_file():
        errors.append("missing internal database-provenance validation report")
    else:
        validation = _json(validation_path)
        if (
            validation.get("result") != "pass"
            or validation.get("error_count") != 0
            or validation.get("warning_count") != 0
            or validation.get("database_provenance_checked") is not True
        ):
            errors.append("Track A validator did not pass cleanly with database provenance")

    if "qa-results" in paths:
        qa_lines = [
            line for line in paths["qa-results"].read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if len(qa_lines) != 100:
            errors.append(f"QA results contain {len(qa_lines)} records, expected 100")
        for number, line in enumerate(qa_lines, 1):
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"QA JSONL line {number}: {exc}")
    if "reasoning-traces" in paths:
        traces = _json(paths["reasoning-traces"])
        if not isinstance(traces, list) or len(traces) != 100:
            errors.append("reasoning traces must be one JSON array of 100 records")

    report_requirements = {
        "metrics-self-report": [
            "§8.4", "p50", "p95", "p99", "cost per query",
            "not self-reported",
        ],
        "operations-report": [
            "concurrency", "hardware", "database", "cost", "configuration",
        ],
        "methodology-summary": [
            "model", "architecture", "isolation", "oracle", "primekg",
        ],
        "clarification-log": [
            "cotiviti responses relied upon", "open questions",
        ],
    }
    for artifact, terms in report_requirements.items():
        if artifact not in paths:
            continue
        folded = paths[artifact].read_text(encoding="utf-8").casefold()
        for term in terms:
            if term.casefold() not in folded:
                errors.append(f"{paths[artifact].name}: missing required topic {term!r}")

    listed = {
        item.get("name"): item
        for item in package.get("required_artifacts", [])
        if isinstance(item, dict)
    }
    for artifact in (
        "qa-results", "reasoning-traces", "metrics-self-report",
        "operations-report", "methodology-summary", "clarification-log",
    ):
        path = paths.get(artifact)
        if path is None:
            continue
        entry = listed.get(path.name)
        if not entry:
            errors.append(f"submission manifest omits {path.name}")
        elif (
            entry.get("sha256") != _sha256(path)
            or entry.get("size") != path.stat().st_size
        ):
            errors.append(f"submission manifest checksum/size mismatch for {path.name}")

    secret_pattern = re.compile(
        rb"(BEGIN (?:RSA |EC )?PRIVATE KEY|security_token_file|"
        rb"MC_DATABASE__PASSWORD\s*[=:]\s*\S+)",
        re.IGNORECASE,
    )
    for path in directory.iterdir():
        if path.is_file() and secret_pattern.search(path.read_bytes()):
            errors.append(f"possible secret material in {path.name}")

    report = {
        "validator": "validate-stage1-track-a-package.py",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": "RFP sections 7.1 and 8.2-8.4, Stage 1 Track A",
        "vendor_id": vendor,
        "version": version,
        "authoritative": package.get("authoritative") is True,
        "result": "pass" if not errors else "fail",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }
    if not args.no_write_report:
        (directory / "rfp-compliance-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
