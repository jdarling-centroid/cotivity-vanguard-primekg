"""Orchestrator QA agent and Finalizer pipeline for Stage 1 evaluation tracks.

This package runs an agentic, multi-hop retrieval loop against the local MCP
tool implementations (calling the Python functions directly to bypass network
overhead) and serialises the results into the evaluation artifacts:

* ``vendor_<vendor_id>_stage1_results_v1.jsonl`` — one JSON Lines record per
  question (Section 8.2 shape).
* ``vendor_<vendor_id>_stage1_traces_v1.json`` — a JSON array of step-by-step
  tool traces (Section 8.3 shape).

The public entry point is :func:`vanguard.shared.agent.runner.main`,
registered as the ``mc-run-eval`` console script.
"""

from __future__ import annotations
