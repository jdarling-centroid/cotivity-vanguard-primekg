"""Deterministic prompt-injection firewall (Category F).

Ports ``deterministic_security_verdict`` from the reference agent's
``llm.py`` (self-contained, no LLM/microservice) and adds a rule for
node-embedded fabricated authority. Fail-closed by construction: queries are
always parameterized and read-only; instructions embedded in question/node text
are never executed.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Verdict:
    malicious: bool
    reason: str | None = None


def _security_text(value: str) -> tuple[str, str, list[str]]:
    canonical = unicodedata.normalize("NFKC", value or "").casefold()
    canonical = "".join(
        ch for ch in canonical if unicodedata.category(ch) != "Cf"
    )
    canonical = canonical.translate(
        str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"})
    )
    words = re.findall(r"[a-z0-9]+", canonical)
    return canonical, " ".join(words), words


def _within_one_edit(value: str, target: str) -> bool:
    if value == target:
        return True
    if abs(len(value) - len(target)) > 1 or min(len(value), len(target)) < 4:
        return False
    if len(value) == len(target):
        diffs = [i for i, (a, b) in enumerate(zip(value, target)) if a != b]
        if len(diffs) == 1:
            return True
        return (
            len(diffs) == 2
            and diffs[1] == diffs[0] + 1
            and value[diffs[0]] == target[diffs[1]]
            and value[diffs[1]] == target[diffs[0]]
        )
    shorter, longer = (value, target) if len(value) < len(target) else (target, value)
    si = li = diffs = 0
    while si < len(shorter) and li < len(longer):
        if shorter[si] == longer[li]:
            si += 1
            li += 1
        else:
            diffs += 1
            li += 1
            if diffs > 1:
                return False
    return True


_PROTECTED = (
    "previous", "prior", "above", "instruction", "instructions", "prompt",
    "system", "developer", "knowledge graph", "primekg", "graph", "tool",
    "tools", "result", "results", "source", "sources", "evidence", "retrieval",
    "context", "document", "documents", "reference data", "safety", "firewall",
    "policy",
)
_HIDDEN = (
    "system prompt", "hidden prompt", "developer message", "internal instruction",
    "secret instruction", "chain of thought", "environment variable", "api key",
    "access token", "credential", "database dump", "all patient data",
    "patient record", "patient records", "retrieved context", "retrieved data",
    "document metadata", "hidden context", "all records",
)


def verdict(question: str) -> Verdict:
    """Fast intent-based verdict. Returns malicious=True with a reason if blocked."""
    canonical, normalized, words = _security_text(question)
    compact = "".join(words)

    def has_fuzzy(*targets: str) -> bool:
        return any(t in compact for t in targets if len(t) >= 6) or any(
            _within_one_edit(w, t) for w in words for t in targets
        )

    # 1) instruction override targeting governed context/evidence
    if has_fuzzy("ignore", "disregard", "bypass", "override", "forget", "skip") and any(
        t in normalized for t in _PROTECTED
    ):
        return Verdict(True, "attempt to override governed instructions or evidence sources")

    # 2) bypass governed retrieval / invent results
    if re.search(
        r"\b(?:do not|don t|never|avoid|without)\b.{0,45}"
        r"\b(?:query|search|use|consult|retrieve|primekg|graph|documents?)\b",
        normalized,
    ) or any(
        p in normalized
        for p in ("hidden model knowledge", "model knowledge instead",
                  "invent the most likely", "without retrieved evidence")
    ):
        return Verdict(True, "attempt to bypass governed retrieval or invent unsupported results")

    # 3) mutate governed graph/db state
    mutation = has_fuzzy(
        "insert", "create", "append", "update", "modify", "delete", "remove", "write"
    )
    governed = any(t in normalized for t in ("edge", "node", "graph", "database", "table", "record", "primekg"))
    if mutation and governed and any(
        p in normalized
        for p in ("before answering", "before responding", "first ", "then return", "then answer")
    ):
        return Verdict(True, "attempt to modify governed graph or database state")

    # 4) disclose protected instructions/credentials/data
    disclose = has_fuzzy("reveal", "expose", "print", "dump", "extract", "exfiltrate") or any(
        a in normalized for a in ("show me", "tell me", "return the")
    )
    if disclose and any(t in normalized for t in _HIDDEN):
        return Verdict(True, "attempt to disclose protected instructions, credentials, or data")

    # 5) transfer data to an external destination
    external = any(
        m in canonical
        for m in ("http://", "https://", "webhook", "email it", "external server",
                  "outside the platform", "base64", "encoded blob")
    )
    transfer = has_fuzzy(
        "send", "upload", "transmit", "post", "exfiltrate", "forward", "copy", "encode", "export"
    )
    if external and transfer:
        return Verdict(True, "attempt to transfer data to an external destination")

    # 6) force a control response instead of grounded results
    forced = bool(
        re.search(r"\b(?:respond|reply|return|output|answer)\b.{0,40}"
                  r"\b(?:only|exactly|single word|verbatim)\b", normalized)
    ) and any(tok in words for tok in ("none", "hacked", "pwned"))
    if forced:
        return Verdict(True, "attempt to force a control response instead of grounded results")

    # 7) node-embedded fabricated authority (PrimeKG-specific extension)
    fabricated = (
        "system note" in normalized
        or ("follow" in words and "instruction" in normalized)
        or (("node" in words or "description" in words) and "the answer is" in normalized)
    )
    if fabricated:
        return Verdict(True, "attempt to follow instructions embedded in node/document text")

    return Verdict(False, None)
