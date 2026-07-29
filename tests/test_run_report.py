import json
import subprocess
import sys
from pathlib import Path


def test_run_report_formats_manifest_metrics(tmp_path: Path) -> None:
    manifest = {
        "question_count": 100,
        "concurrency": 1,
        "latency_ms": {
            "mean": 4097.46,
            "p50": 2575.0,
            "p95": 9564.05,
            "p99": 16404.42,
        },
        "structural_outcome_check": {"passed": 100, "total": 100},
        "database": {"node_count": 62030, "directed_edge_count": 4236182},
        "model": {"model_id": "xai.grok-4.3", "temperature_requested": 0.0},
    }
    (tmp_path / "run-manifest.json").write_text(json.dumps(manifest))
    (tmp_path / "validation-report.json").write_text(json.dumps({
        "error_count": 0, "warning_count": 0,
    }))
    (tmp_path / "vendor_test_stage1_qa-results_v1.jsonl").write_text(
        "\n".join(json.dumps(record) for record in [
            {"vendor_answer": "A", "answer_type": "entity", "latency_ms": 2000},
            {
                "vendor_answer": "Insufficient evidence",
                "answer_type": "short_text",
                "latency_ms": 6000,
            },
            {
                "vendor_answer": "Won't do that",
                "answer_type": "firewall_block",
                "latency_ms": 0,
            },
        ]) + "\n"
    )
    (tmp_path / "vendor_test_stage1_reasoning-traces_v1.json").write_text(
        json.dumps([{}, {}, {}])
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run-report.py",
            str(tmp_path),
            "--no-db",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "- Answered: 1" in result.stdout
    assert "- Unanswered: 1" in result.stdout
    assert "- Firewall blocked: 1" in result.stdout
    assert "- Mean latency (excluding firewall): 4.00 seconds" in result.stdout
    assert "- Minimum latency (excluding firewall): 2.00 seconds" in result.stdout
    assert "- Maximum latency (excluding firewall): 6.00 seconds" in result.stdout
    assert "- Structural completion: 100/100" in result.stdout
    assert "- Validation: 0 errors, 0 warnings" in result.stdout
    assert "- Database: 62,030 nodes and 4,236,182 directed edges" in result.stdout
    assert "- Model: xai.grok-4.3, temperature 0" in result.stdout
