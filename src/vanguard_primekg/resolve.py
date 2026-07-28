"""Entity resolution: question label -> PrimeKG node id.

Lexical-first and type-scoped (Decision #3). Exact normalized match handles
almost every question because the questions name entities close to the PrimeKG
node text; a guarded substring fallback covers minor wording gaps. Vector
similarity (optional ``name_vec``) is the last resort.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import oracledb

from .load_primekg import normalize_name

_TRAILING_PAREN = re.compile(r"\s*\([^)]*\)\s*$")

# Radiolabeled-tracer prefixes, e.g. "(1,2,6,7-3H)Testosterone". PrimeKG models
# the pharmacology (targets, carriers) on the parent compound, so a tracer
# resolves to its parent. Restricted to explicit isotope tokens so stereo
# descriptors like "(2S)-..." are never stripped.
_ISOTOPES = r"2H|3H|11C|13C|14C|13N|15N|18O|32P|33P|35S|18F|123I|125I|131I"
_ISOTOPE_PREFIX = re.compile(rf"^\([^)]*\b(?:{_ISOTOPES})\b[^)]*\)\s*", re.I)


def _isotope_parent(name: str) -> str | None:
    m = _ISOTOPE_PREFIX.match(name.strip())
    if not m:
        return None
    parent = name.strip()[m.end():].strip()
    return parent or None


@dataclass(frozen=True)
class ResolvedEntity:
    node_id: str
    name: str
    node_type: str
    method: str
    score: float


def _variants(name: str) -> list[str]:
    """Normalized match candidates for a label (with/without a trailing paren)."""
    base = normalize_name(name)
    out = [base]
    stripped = normalize_name(_TRAILING_PAREN.sub("", name))
    if stripped and stripped != base:
        out.append(stripped)
    if not _TRAILING_PAREN.search(name):
        out.append(normalize_name(f"{name} (disease)"))
    # de-dup, preserve order
    seen: set[str] = set()
    return [v for v in out if v and not (v in seen or seen.add(v))]


class Resolver:
    def __init__(self, conn: oracledb.Connection) -> None:
        self._conn = conn

    def _query(self, sql: str, binds: dict) -> list[tuple]:
        with self._conn.cursor() as cur:
            cur.execute(sql, binds)
            return cur.fetchall()

    def resolve(
        self, name: str, types: tuple[str, ...] = ()
    ) -> ResolvedEntity | None:
        # Radiolabeled tracer -> parent compound (PrimeKG holds the pharmacology
        # on the parent). Try the parent first; fall back to the literal name.
        parent = _isotope_parent(name)
        if parent is not None:
            hit = self.resolve(parent, types)
            if hit is not None:
                return hit

        variants = _variants(name)
        var_binds = {f"v{i}": v for i, v in enumerate(variants)}
        var_list = ", ".join(f":{k}" for k in var_binds)

        # 1) exact normalized match, scoped by type, shortest name wins.
        if types:
            type_binds = {f"t{i}": t for i, t in enumerate(types)}
            type_list = ", ".join(f":{k}" for k in type_binds)
            rows = self._query(
                f"SELECT node_id, name, node_type FROM pk_nodes "
                f"WHERE name_norm IN ({var_list}) AND node_type IN ({type_list}) "
                f"ORDER BY LENGTH(name)",
                {**var_binds, **type_binds},
            )
            if rows:
                return ResolvedEntity(*rows[0], method="exact_typed", score=1.0)

        # 2) exact normalized match, any type.
        rows = self._query(
            f"SELECT node_id, name, node_type FROM pk_nodes "
            f"WHERE name_norm IN ({var_list}) ORDER BY LENGTH(name)",
            var_binds,
        )
        if rows:
            return ResolvedEntity(*rows[0], method="exact", score=0.95)

        # 2b) space-insensitive match (handles spacing gaps like "]METHANOL").
        compact = normalize_name(_TRAILING_PAREN.sub("", name)).replace(" ", "")
        if len(compact) >= 5:
            if types:
                type_binds = {f"t{i}": t for i, t in enumerate(types)}
                type_list = ", ".join(f":{k}" for k in type_binds)
                rows = self._query(
                    f"SELECT node_id, name, node_type FROM pk_nodes "
                    f"WHERE REPLACE(name_norm, ' ', '') = :cmp "
                    f"AND node_type IN ({type_list}) ORDER BY LENGTH(name)",
                    {**type_binds, "cmp": compact},
                )
                if rows:
                    return ResolvedEntity(*rows[0], method="compact_typed", score=0.85)
            rows = self._query(
                "SELECT node_id, name, node_type FROM pk_nodes "
                "WHERE REPLACE(name_norm, ' ', '') = :cmp ORDER BY LENGTH(name)",
                {"cmp": compact},
            )
            if rows:
                return ResolvedEntity(*rows[0], method="compact", score=0.8)

        # 3) guarded substring fallback, scoped by type, shortest name wins.
        base = normalize_name(_TRAILING_PAREN.sub("", name))
        if types and len(base) >= 4:
            type_binds = {f"t{i}": t for i, t in enumerate(types)}
            type_list = ", ".join(f":{k}" for k in type_binds)
            rows = self._query(
                f"SELECT node_id, name, node_type FROM pk_nodes "
                f"WHERE node_type IN ({type_list}) "
                f"AND name_norm LIKE :pat ESCAPE '\\' ORDER BY LENGTH(name) "
                f"FETCH FIRST 1 ROWS ONLY",
                {**type_binds, "pat": f"{_like_escape(base)}%"},
            )
            if rows:
                return ResolvedEntity(*rows[0], method="prefix_typed", score=0.7)

        # 4) fuzzy: match on the most distinctive token (handles loose ad-hoc
        # phrasings like "tourettes ticks" -> "Tourette syndrome"). Type-scoped,
        # shortest matching name wins. Best-effort; the resolved name is shown.
        if types:
            tokens = sorted(
                (t for t in re.split(r"[^a-z0-9]+", base) if len(t) >= 5 and t not in _STOPWORDS),
                key=len,
                reverse=True,
            )
            if tokens:
                type_binds = {f"t{i}": t for i, t in enumerate(types)}
                type_list = ", ".join(f":{k}" for k in type_binds)
                for tok in (tokens[0], tokens[0].rstrip("s")):
                    if len(tok) < 5:
                        continue
                    rows = self._query(
                        f"SELECT node_id, name, node_type FROM pk_nodes "
                        f"WHERE node_type IN ({type_list}) "
                        f"AND name_norm LIKE :pat ESCAPE '\\' ORDER BY LENGTH(name) "
                        f"FETCH FIRST 1 ROWS ONLY",
                        {**type_binds, "pat": f"%{_like_escape(tok)}%"},
                    )
                    if rows:
                        return ResolvedEntity(*rows[0], method="fuzzy_token", score=0.5)

        return None


_STOPWORDS = {
    "disease", "diseases", "drug", "drugs", "protein", "proteins", "gene", "genes",
    "syndrome", "disorder", "common", "known", "with", "that", "have", "from",
}


def _like_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
