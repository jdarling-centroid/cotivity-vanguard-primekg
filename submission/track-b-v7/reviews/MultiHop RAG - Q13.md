# MultiHop RAG - Q13

**Question ID:** `Q-MH-013`

**Question:** What team was eliminated from European competitions after a loss at Old Trafford, as reported by both 'The Independent - Sports' and 'Sporting News'?

- category: `multi_hop_traversal`
- answer type: `entity`
- confidence: `0.8`
- confidence basis: `model_synthesis_bounded_to_oracle_retrieved_public_passages`
- latency: `7215 ms`
- truncated: `None`
- reasoning trace: `T-MH-013`

## Answer

Manchester United

## Answer support

- `mh_e_b1423a09aead9250366c`
- `mh_e_e867cb881ea163b71d02`
- `mh_e_b8b738705fd22b3963b1`
- `mh_n_chunk_45d84247882712f7defc`
- `mh_n_chunk_0b5280a51c632047e3d6`
- `mh_n_chunk_7479ffbb389eb5eb4a33`

## Reasoning and evidence path

### 1. `firewall_check`

Status: **allowed**; executed before planner: `None`.

### 2. `bounded_search_expansion`

```json
{
  "error": null,
  "operation": "bounded_search_expansion",
  "search_terms": []
}
```

### 3. `oracle_graph_retrieval`

```json
{
  "operation": "oracle_graph_retrieval",
  "queries": [
    {
      "binds": {
        "c0_0": "team",
        "c0_1": "eliminated",
        "c0_2": "european",
        "c0_3": "competitions",
        "c0_4": "after",
        "c0_5": "loss",
        "c0_6": "old",
        "c0_7": "trafford",
        "limit": 300,
        "s0": "the independent - sports",
        "s1": "sporting news",
        "seed_limit": 30,
        "t0": "team",
        "t1": "eliminated",
        "t10": "sporting",
        "t11": "news",
        "t2": "european",
        "t3": "competitions",
        "t4": "after",
        "t5": "loss",
        "t6": "old",
        "t7": "trafford",
        "t8": "independent",
        "t9": "sports"
      },
      "chunk_count": 20,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 18 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 9 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 2 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_2) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_2) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_3) > 0 THEN 40 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_3) > 0 THEN 20 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_4) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_4) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_5) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_5) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_6) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_6) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_7) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_7) > 0 THEN 12 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
    }
  ],
  "query_count": 1,
  "read_only": true,
  "retrieved_chunk_count": 20
}
```

### 4. `edge_traversal`

```json
{
  "edge_id": "mh_e_b1423a09aead9250366c",
  "evidence": {
    "doc_id": "mh_doc_9390303c3db8ea043e85",
    "page": 1,
    "span": [
      3929,
      4174
    ]
  },
  "from": "mh_n_doc_9390303c3db8ea043e85",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_45d84247882712f7defc"
}
```

### 5. `edge_traversal`

```json
{
  "edge_id": "mh_e_e867cb881ea163b71d02",
  "evidence": {
    "doc_id": "mh_doc_9390303c3db8ea043e85",
    "page": 1,
    "span": [
      3150,
      3230
    ]
  },
  "from": "mh_n_doc_9390303c3db8ea043e85",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_0b5280a51c632047e3d6"
}
```

### 6. `edge_traversal`

```json
{
  "edge_id": "mh_e_b8b738705fd22b3963b1",
  "evidence": {
    "doc_id": "mh_doc_660e07f75a5f0260a214",
    "page": 1,
    "span": [
      2412,
      2948
    ]
  },
  "from": "mh_n_doc_660e07f75a5f0260a214",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_7479ffbb389eb5eb4a33"
}
```

### 7. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_45d84247882712f7defc",
    "mh_n_chunk_0b5280a51c632047e3d6",
    "mh_n_chunk_7479ffbb389eb5eb4a33"
  ],
  "claim": "Manchester United eliminated from Champions League after loss to Bayern at Old Trafford",
  "operation": "evidence_synthesis"
}
```

### 8. `grounded_finalization`

```json
{
  "answer_derived_only_from_cited_chunks": true,
  "operation": "grounded_finalization"
}
```

## Graph elements used

### Nodes

- `mh_n_doc_9390303c3db8ea043e85`
- `mh_n_chunk_45d84247882712f7defc`
- `mh_n_chunk_0b5280a51c632047e3d6`
- `mh_n_doc_660e07f75a5f0260a214`
- `mh_n_chunk_7479ffbb389eb5eb4a33`

### Edges

- `mh_e_b1423a09aead9250366c`
- `mh_e_e867cb881ea163b71d02`
- `mh_e_b8b738705fd22b3963b1`

## Citations

```json
[
  {
    "doc_id": "mh_doc_9390303c3db8ea043e85",
    "node_id": "mh_n_chunk_45d84247882712f7defc",
    "page": 1,
    "span": [
      3929,
      4174
    ]
  },
  {
    "doc_id": "mh_doc_9390303c3db8ea043e85",
    "node_id": "mh_n_chunk_0b5280a51c632047e3d6",
    "page": 1,
    "span": [
      3150,
      3230
    ]
  },
  {
    "doc_id": "mh_doc_660e07f75a5f0260a214",
    "node_id": "mh_n_chunk_7479ffbb389eb5eb4a33",
    "page": 1,
    "span": [
      2412,
      2948
    ]
  }
]
```

## Retrieved context

```json
[
  {
    "doc_id": "mh_doc_9390303c3db8ea043e85",
    "node_id": "mh_n_chunk_45d84247882712f7defc",
    "page": 1,
    "snippet": "It didn\u2019t help that Bruno Fernandes blazed United\u2019s best opportunity over the bar after good work from Aaron Wan Bissaka. It looked like it was going to be one of those games. It certainly wasn\u2019t one of those big European nights at Old Trafford.",
    "span": [
      3929,
      4174
    ]
  },
  {
    "doc_id": "mh_doc_9390303c3db8ea043e85",
    "node_id": "mh_n_chunk_0b5280a51c632047e3d6",
    "page": 1,
    "snippet": "Harry Kane\u2019s assist was another reminder of what could have been for United (PA)",
    "span": [
      3150,
      3230
    ]
  },
  {
    "doc_id": "mh_doc_660e07f75a5f0260a214",
    "node_id": "mh_n_chunk_7479ffbb389eb5eb4a33",
    "page": 1,
    "snippet": "Instead, they are cast out of continental competition altogether. Europe\u2019s sinking superpower have become just the fourth English team to prop up a Champions League group when it concluded. There was something predictable about the manner of their demise; their defence was unlocked by Harry Kane, with a lovely flick. The England captain is the forward United neglected to bid for in the summer. The one they did buy, Hojlund, has at least struck in the Champions League but in domestic competitions he has been outscored 18-0 by Kane.",
    "span": [
      2412,
      2948
    ]
  }
]
```
