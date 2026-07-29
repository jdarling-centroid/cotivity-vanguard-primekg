"""One-query lexical retrieval over the constructed Track B Oracle graph."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9'.-]{2,}")
_STOP = {
    "about", "according", "also", "among", "and", "are", "been", "being",
    "both", "but", "company", "considering", "could", "does", "each", "for",
    "from", "had", "has", "have", "how", "individual", "into", "its", "known",
    "name", "not", "reported", "reports", "that", "the", "their", "then", "this",
    "those", "through", "was", "were", "what", "when", "where", "which", "while",
    "who", "with", "would",
}


def clause_queries(question: str) -> list[str]:
    """Extract clue-bearing halves using the prior Track B baseline strategy."""
    cleaned = re.sub(
        r",\s*according to articles? from .*?,\s*",
        " ",
        question,
        count=1,
        flags=re.IGNORECASE,
    )
    parts = re.split(
        r"(?:\s+and\s+['‘\"][^'’\"]+['’\"](?:\s+for)?\s+|"
        r"(?:,\s+|\s+and\s+)(?:and\s+)?"
        r"(?:is|are|was|were|has|have|might|would|could|provided|"
        r"['‘\"]?the\s+[A-Z])\s+(?:also\s+)?)",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )
    queries: list[str] = []
    for part in parts:
        query = part.strip(" ?")
        query = re.sub(
            r"^(?:which|what|who)\b.*?\b(?:that is|who is|known for)\s+",
            "",
            query,
            count=1,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r",?\s+(?:as\s+reported\s+by|according\s+to)\b.*$",
            "",
            query,
            count=1,
            flags=re.IGNORECASE,
        ).strip(" ,")
        if len(query) >= 24:
            queries.append(query)
    return queries


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_node_id: str
    document_node_id: str
    contains_edge_id: str
    text: str
    provenance: dict
    document: dict
    score: int


def search_tokens(question: str, *, limit: int = 24) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for match in _TOKEN.finditer(question):
        token = match.group(0).casefold().strip(".'-")
        if len(token) < 3 or token in _STOP or token in seen:
            continue
        seen.add(token)
        values.append(token)
    # Later clauses in the issued questions often contain the disambiguating
    # bridge. Retain both ends when the question exceeds the bounded token cap.
    if len(values) > limit:
        half = limit // 2
        values = values[:half] + values[-(limit - half):]
    return values


def retrieve(
    conn,
    question: str,
    *,
    limit: int = 24,
    known_sources: set[str] | None = None,
    search_expansion: list[str] | None = None,
    evidence_queries: list[str] | None = None,
) -> tuple[list[RetrievedChunk], str, dict]:
    """Return top text blocks and their Document->TextBlock graph edge in one SQL."""
    candidate_tokens = search_tokens(" ".join(search_expansion or []), limit=12)
    evidence_tokens = search_tokens(" ".join(evidence_queries or []), limit=24)
    expansion_tokens = list(dict.fromkeys([
        *candidate_tokens,
        *evidence_tokens,
    ]))
    question_tokens = search_tokens(question, limit=24)
    tokens = list(dict.fromkeys([*expansion_tokens, *question_tokens]))
    if not tokens:
        return [], "", {}
    # Retrieve a bounded superset, then deterministically balance passages
    # across publishers explicitly named in the question.
    binds: dict[str, object] = {
        "limit": max(300, limit * 10),
        "seed_limit": max(300 if evidence_queries else 30, limit),
    }
    score_parts: list[str] = []
    match_parts: list[str] = []
    for index, token in enumerate(tokens):
        key = f"t{index}"
        binds[key] = token
        body_expression = f"INSTR(LOWER(n.text_content), :{key})"
        title_expression = (
            "INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')),"
            f" :{key})"
        )
        expression = f"GREATEST({body_expression},{title_expression})"
        weight = max(1, min(len(token), 12) - 2)
        if index < len(candidate_tokens):
            weight += 6
        score_parts.append(
            f"CASE WHEN {body_expression} > 0 THEN {weight * 2} "
            f"WHEN {title_expression} > 0 THEN {weight} ELSE 0 END"
        )
        match_parts.append(f"{expression} > 0")
    literal_phrases = [
        value.strip().casefold()
        for value in re.findall(r"['‘\"]([^'’\"]{2,80})['’\"]", question)
    ]
    quoted = list(literal_phrases)
    question_folded = question.casefold()
    for source in sorted(known_sources or set(), key=len, reverse=True):
        folded = source.casefold()
        if folded in question_folded and folded not in quoted:
            quoted.append(folded)
    source_flag = "0"
    source_partition = "'__all__'"
    if quoted:
        source_terms: list[str] = []
        for index, value in enumerate(quoted):
            key = f"s{index}"
            binds[key] = value
            source_terms.append(f":{key}")
        source_flag = (
            "CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN ("
            + ",".join(source_terms) + ") THEN 1 ELSE 0 END"
        )
        source_partition = "JSON_VALUE(n.attributes_json,'$.source')"
    score_options = ["(" + " + ".join(score_parts) + ")"]
    scoring_clauses = list(dict.fromkeys([
        *clause_queries(question),
        *(evidence_queries or []),
    ]))
    for clause_index, clause in enumerate(scoring_clauses):
        clause_parts: list[str] = []
        for token_index, token in enumerate(search_tokens(clause, limit=16)):
            key = f"c{clause_index}_{token_index}"
            binds[key] = token
            weight = max(1, min(len(token), 12) - 2)
            clause_parts.append(
                "CASE WHEN INSTR(LOWER(n.text_content), "
                f":{key}) > 0 THEN {weight * 4} "
                "WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')),"
                f" :{key}) > 0 THEN {weight * 2} ELSE 0 END"
            )
        if clause_parts:
            score_options.append("(" + " + ".join(clause_parts) + ")")
    score = (
        score_options[0]
        if len(score_options) == 1
        else "GREATEST(" + ",".join(score_options) + ")"
    )
    sql = (
        "WITH ranked AS ("
        " SELECT n.node_id chunk_id,n.text_content,n.provenance_json,"
        f" ({score}) score,{source_flag} source_match,"
        " JSON_VALUE(n.provenance_json,'$.doc_id') doc_id,"
        f" {source_partition} source_name"
        " FROM mh_nodes n WHERE n.node_type='TextBlock' AND ("
        + " OR ".join(match_parts)
        + ")), document_ranked AS ("
        " SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id"
        " ORDER BY score DESC,chunk_id) document_rank FROM ranked r"
        "), source_ranked AS ("
        " SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name"
        " ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r"
        " WHERE document_rank=1"
        "), seeds AS ("
        " SELECT * FROM source_ranked"
        " ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END,"
        " score DESC,source_rank,chunk_id"
        " FETCH FIRST :seed_limit ROWS ONLY"
        "), top_document_seeds AS ("
        " SELECT * FROM seeds"
        " ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id"
        " FETCH FIRST 20 ROWS ONLY"
        "), expanded_ids AS ("
        " SELECT related.subject_id chunk_id,MAX(s.score)-1 score"
        " FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id"
        " AND mention.predicate='mentions'"
        " JOIN mh_edges related ON related.object_id=mention.object_id"
        " AND related.predicate='mentions'"
        " GROUP BY related.subject_id"
        "), document_expanded_ids AS ("
        " SELECT sibling.object_id chunk_id,r.score"
        " FROM top_document_seeds s"
        " JOIN mh_edges parent ON parent.object_id=s.chunk_id"
        " AND parent.predicate='contains_chunk'"
        " JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id"
        " AND sibling.predicate='contains_chunk'"
        " JOIN ranked r ON r.chunk_id=sibling.object_id"
        "), candidate_ids AS ("
        " SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ("
        " SELECT chunk_id,score,0 priority FROM seeds UNION ALL"
        " SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL"
        " SELECT chunk_id,score,0 priority FROM document_expanded_ids)"
        " GROUP BY chunk_id"
        "), candidate_ranked AS ("
        " SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority,"
        f" {source_flag} source_match,"
        f" ROW_NUMBER() OVER (PARTITION BY {source_partition}"
        " ORDER BY c.score DESC,c.chunk_id) source_rank"
        " FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id"
        "), top_chunks AS ("
        " SELECT * FROM candidate_ranked"
        " ORDER BY priority,"
        " CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END,"
        " score DESC,source_rank,chunk_id"
        " FETCH FIRST :limit ROWS ONLY)"
        " SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content,"
        " t.provenance_json,d.attributes_json,d.label,t.score"
        " FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id"
        " AND e.predicate='contains_chunk'"
        " JOIN mh_nodes d ON d.node_id=e.subject_id"
        " ORDER BY t.score DESC,t.chunk_id"
    )
    rows: list[RetrievedChunk] = []
    def decoded(value) -> dict:
        if isinstance(value, dict):
            return value
        raw = value.read() if hasattr(value, "read") else value
        return json.loads(raw or "{}")

    with conn.cursor() as cursor:
        cursor.execute(sql, binds)
        for row in cursor.fetchall():
            text = row[3].read() if hasattr(row[3], "read") else str(row[3])
            rows.append(
                RetrievedChunk(
                    chunk_node_id=row[0],
                    document_node_id=row[1],
                    contains_edge_id=row[2],
                    text=text,
                    provenance=decoded(row[4]),
                    document={**decoded(row[5]), "title": row[6]},
                    score=int(row[7]),
                )
            )
    # Candidate expansion intentionally boosts entity recall, which can leave
    # many paragraphs from the same entity/document tied. Break those ties
    # deterministically with the original question only so answer-bearing
    # paragraphs outrank unrelated mentions of the candidate entity.
    original_tokens = search_tokens(question, limit=24)

    def original_clue_score(row: RetrievedChunk) -> int:
        body = row.text.casefold()
        title = str(row.document.get("title") or "").casefold()
        return sum(
            (max(1, min(len(token), 12) - 2) * 2 if token in body else 0)
            + (max(1, min(len(token), 12) - 2) if token in title else 0)
            for token in original_tokens
        )

    rows.sort(
        key=lambda row: (
            -row.score,
            -original_clue_score(row),
            row.chunk_node_id,
        )
    )
    # Reserve a small evidence lane for each independently planned factual leg.
    # This prevents a frequent entity (for example, a company mentioned across
    # a long article) from consuming every final passage slot.
    literal_anchors = list(dict.fromkeys([
        *literal_phrases,
        *(
            token for token in search_tokens(question, limit=40)
            if any(char.isdigit() for char in token)
        ),
    ]))
    clue_selected: list[RetrievedChunk] = []
    clue_used: set[str] = set()
    for anchor in literal_anchors:
        row = next(
            (
                item for item in rows
                if anchor in item.text.casefold()
                or anchor in str(item.document.get("title") or "").casefold()
            ),
            None,
        )
        if row is not None and row.chunk_node_id not in clue_used:
            clue_selected.append(row)
            clue_used.add(row.chunk_node_id)
    for clue in evidence_queries or clause_queries(question):
        clue_tokens = search_tokens(clue, limit=16)
        if not clue_tokens:
            continue

        def clue_score(row: RetrievedChunk) -> int:
            body = row.text.casefold()
            title = str(row.document.get("title") or "").casefold()
            lexical = sum(
                (max(1, min(len(token), 12) - 2) * 3 if token in body else 0)
                + (max(1, min(len(token), 12) - 2) if token in title else 0)
                for token in clue_tokens
            )
            candidate_bonus = sum(
                (len(candidate_tokens) - index) * 20
                for index, token in enumerate(candidate_tokens)
                if token in body or token in title
            )
            return lexical + candidate_bonus

        added = 0
        clue_documents: set[str] = set()
        for row in sorted(
            rows,
            key=lambda item: (
                -clue_score(item),
                -item.score,
                item.chunk_node_id,
            ),
        ):
            row_body = row.text.casefold()
            row_title = str(row.document.get("title") or "").casefold()
            if not any(
                token in row_body or token in row_title
                for token in clue_tokens
            ):
                break
            if (
                row.chunk_node_id in clue_used
                or row.document_node_id in clue_documents
            ):
                continue
            clue_selected.append(row)
            clue_used.add(row.chunk_node_id)
            clue_documents.add(row.document_node_id)
            added += 1
            if added >= 2:
                break
    if not quoted:
        selected = clue_selected[:limit]
        selected_ids = {row.chunk_node_id for row in selected}
        selected.extend(
            row for row in rows
            if row.chunk_node_id not in selected_ids
        )
        return selected[:limit], sql, binds
    selected: list[RetrievedChunk] = clue_selected[:limit]
    used: set[str] = {row.chunk_node_id for row in selected}
    used_documents: set[str] = {row.document_node_id for row in selected}
    per_source = max(2, (limit // 2) // max(1, len(quoted)))
    for source in quoted:
        for row in rows:
            if len([item for item in selected if item.document.get("source", "").casefold() == source]) >= per_source:
                break
            if (
                row.chunk_node_id not in used
                and row.document_node_id not in used_documents
                and row.document.get("source", "").casefold() == source
            ):
                selected.append(row)
                used.add(row.chunk_node_id)
                used_documents.add(row.document_node_id)
    # Add additional high-scoring blocks from the strongest documents. A
    # document's answer-bearing paragraph is often different from its
    # title-matching paragraph.
    selected_document_order = list(
        dict.fromkeys(item.document_node_id for item in selected)
    )
    for document_id in selected_document_order:
        if len(selected) >= limit * 3 // 4:
            break
        added_for_document = 0
        for row in (
                item for item in rows
                if item.document_node_id == document_id
                and item.chunk_node_id not in used
        ):
            if len(selected) >= limit * 3 // 4 or added_for_document >= 3:
                break
            selected.append(row)
            used.add(row.chunk_node_id)
            added_for_document += 1
    # Preserve room for graph-expanded evidence from publishers that were not
    # named explicitly in the question.
    for row in rows:
        if len(selected) >= limit:
            break
        row_source = row.document.get("source", "").casefold()
        if (
            row_source not in quoted
            and row.document_node_id not in used_documents
            and row.chunk_node_id not in used
        ):
            selected.append(row)
            used.add(row.chunk_node_id)
            used_documents.add(row.document_node_id)
    for row in rows:
        if len(selected) >= limit:
            break
        if row.chunk_node_id not in used:
            selected.append(row)
            used.add(row.chunk_node_id)
    return selected[:limit], sql, binds
