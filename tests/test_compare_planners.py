from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _write(directory: Path, *, status: str, answer_nodes: list[str], op: str = "expand") -> None:
    directory.mkdir()
    (directory / "run-manifest.json").write_text(
        json.dumps(
            {
                "questions": [
                    {
                        "question_id": "Q-KG-001",
                        "status": status,
                        "plan": {"op": op},
                        "answer_node_ids": answer_nodes,
                        "truncated": False,
                    }
                ]
            }
        )
    )


def test_compare_planners_reports_exact_match(tmp_path: Path) -> None:
    left, right = tmp_path / "regex", tmp_path / "agent"
    _write(left, status="answered_with_evidence", answer_nodes=["b", "a"])
    _write(right, status="answered_with_evidence", answer_nodes=["a", "b"])
    completed = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "compare-planners.py"), str(left), str(right)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["divergence_count"] == 0


def test_compare_planners_marks_divergence_for_review(tmp_path: Path) -> None:
    left, right = tmp_path / "regex", tmp_path / "agent"
    _write(left, status="answered_with_evidence", answer_nodes=["a"])
    _write(right, status="refused", answer_nodes=[])
    completed = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "compare-planners.py"), str(left), str(right)],
        text=True,
        capture_output=True,
        check=False,
    )
    report = json.loads(completed.stdout)
    assert completed.returncode == 3
    assert report["comparison_type"] == "regression_review_not_accuracy"
    assert report["divergences"][0]["disposition"] == "requires_review"
