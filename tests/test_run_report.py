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
        "token_usage": {
            "input_tokens": 1000,
            "output_tokens": 200,
            "total_tokens": 1200,
            "requests": 2,
        },
        "cost_per_query": {
            "model_cost_usd_total": 0.00175,
            "model_cost_usd_per_query": 0.0000175,
            "pricing_basis": {
                "input_usd_per_million_tokens": 1.25,
                "output_usd_per_million_tokens": 2.5,
            },
        },
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
    assert "- Outcomes recorded: 3/100" in result.stdout
    assert "- Structural checks: 100/100" in result.stdout
    assert "- Validation: PASS — 0 errors, 0 warnings" in result.stdout
    assert "- Database: 62,030 nodes and 4,236,182 directed edges" in result.stdout
    assert "- Model: xai.grok-4.3, temperature 0" in result.stdout
    assert "- Input tokens: 1,000" in result.stdout
    assert "- Output tokens: 200" in result.stdout
    assert "- Model cost total: $0.00175000" in result.stdout


def test_run_report_recalculates_cost_with_overrides(tmp_path: Path) -> None:
    manifest = {
        "question_count": 2,
        "token_usage": {
            "input_tokens": 1_000_000,
            "output_tokens": 500_000,
            "total_tokens": 1_500_000,
            "requests": 2,
        },
    }
    (tmp_path / "run-manifest.json").write_text(json.dumps(manifest))

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run-report.py",
            str(tmp_path),
            "--input-cost-per-million",
            "2",
            "--output-cost-per-million",
            "4",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "- Model cost total: $4.00000000" in result.stdout
    assert "- Model cost per question: $2.00000000" in result.stdout
    assert "- Cost basis: $2/M input, $4/M output" in result.stdout


def test_run_report_reads_packaged_completion_counts(tmp_path: Path) -> None:
    (tmp_path / "run-manifest.json").write_text(json.dumps({
        "question_count": 100,
        "completion": {
            "structural_passed": 99,
            "structural_total": 100,
        },
    }))

    result = subprocess.run(
        [sys.executable, "scripts/run-report.py", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "- Structural checks: 99/100" in result.stdout
