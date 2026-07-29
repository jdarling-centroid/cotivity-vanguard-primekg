# MultiHop RAG - Q34

**Question ID:** `Q-MH-034`

**Question:** Who is the individual under 30 that was once the richest in the world, associated with the cryptocurrency platform FTX, and is facing allegations of fraud according to TechCrunch?

- category: `multi_hop_traversal`
- answer type: `entity`
- confidence: `0.9`
- confidence basis: `model_synthesis_bounded_to_oracle_retrieved_public_passages`
- latency: `6866 ms`
- truncated: `None`
- reasoning trace: `T-MH-034`

## Answer

Sam Bankman-Fried (SBF)

## Answer support

- `mh_e_5332365adb966e0f92ec`
- `mh_e_7371e59af3c2f5d8bd96`
- `mh_n_chunk_3779da42c5a9062b91a7`
- `mh_n_chunk_9eb6890e17257a2eac2c`

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
        "c0_0": "under",
        "c0_1": "once",
        "c0_2": "richest",
        "c0_3": "world",
        "c0_4": "associated",
        "c0_5": "cryptocurrency",
        "c0_6": "platform",
        "c0_7": "ftx",
        "c1_0": "facing",
        "c1_1": "allegations",
        "c1_2": "fraud",
        "limit": 300,
        "s0": "techcrunch",
        "seed_limit": 30,
        "t0": "under",
        "t1": "once",
        "t10": "fraud",
        "t11": "techcrunch",
        "t2": "richest",
        "t3": "world",
        "t4": "associated",
        "t5": "cryptocurrency",
        "t6": "platform",
        "t7": "ftx",
        "t8": "facing",
        "t9": "allegations"
      },
      "chunk_count": 20,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 18 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 9 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 8 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_2) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_2) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_3) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_3) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_4) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_4) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_5) > 0 THEN 40 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_5) > 0 THEN 20 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_6) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_6) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_7) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_7) > 0 THEN 2 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c1_0) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_0) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_1) > 0 THEN 36 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_1) > 0 THEN 18 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_2) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_2) > 0 THEN 6 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
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
  "edge_id": "mh_e_5332365adb966e0f92ec",
  "evidence": {
    "doc_id": "mh_doc_8438207b101080d5ea97",
    "page": 1,
    "span": [
      0,
      312
    ]
  },
  "from": "mh_n_doc_8438207b101080d5ea97",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_3779da42c5a9062b91a7"
}
```

### 5. `edge_traversal`

```json
{
  "edge_id": "mh_e_7371e59af3c2f5d8bd96",
  "evidence": {
    "doc_id": "mh_doc_eb046c4ddbd31a8f9e77",
    "page": 1,
    "span": [
      6198,
      6560
    ]
  },
  "from": "mh_n_doc_eb046c4ddbd31a8f9e77",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_9eb6890e17257a2eac2c"
}
```

### 6. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_3779da42c5a9062b91a7"
  ],
  "claim": "SBF/FTX founder accused of orchestrating one of the biggest financial frauds in American history via FTX collapse",
  "operation": "evidence_synthesis"
}
```

### 7. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_9eb6890e17257a2eac2c"
  ],
  "claim": "Prosecution painted Bankman-Fried as knowingly committing fraud for great wealth/power via FTX trial coverage",
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

- `mh_n_doc_8438207b101080d5ea97`
- `mh_n_chunk_3779da42c5a9062b91a7`
- `mh_n_doc_eb046c4ddbd31a8f9e77`
- `mh_n_chunk_9eb6890e17257a2eac2c`

### Edges

- `mh_e_5332365adb966e0f92ec`
- `mh_e_7371e59af3c2f5d8bd96`

## Citations

```json
[
  {
    "doc_id": "mh_doc_8438207b101080d5ea97",
    "node_id": "mh_n_chunk_3779da42c5a9062b91a7",
    "page": 1,
    "span": [
      0,
      312
    ]
  },
  {
    "doc_id": "mh_doc_eb046c4ddbd31a8f9e77",
    "node_id": "mh_n_chunk_9eb6890e17257a2eac2c",
    "page": 1,
    "span": [
      6198,
      6560
    ]
  }
]
```

## Retrieved context

```json
[
  {
    "doc_id": "mh_doc_8438207b101080d5ea97",
    "node_id": "mh_n_chunk_3779da42c5a9062b91a7",
    "page": 1,
    "snippet": "Come Tuesday, our eyes will be trained on the Manhattan Federal Court for the trial of Sam Bankman-Fried, the disgraced cryptocurrency entrepreneur accused of orchestrating \u201cone of the biggest financial frauds in American history\u201d: the multibillion-dollar collapse of FTX, the crypto exchange he founded and led.",
    "span": [
      0,
      312
    ]
  },
  {
    "doc_id": "mh_doc_eb046c4ddbd31a8f9e77",
    "node_id": "mh_n_chunk_9eb6890e17257a2eac2c",
    "page": 1,
    "snippet": "Inside the SBF trial: Rebecca and Jacquelyn report on the second day of the SBF and FTX trial. The prosecution painted Bankman-Fried as someone who knowingly committed fraud to achieve great wealth, power and influence, while the defense countered that the FTX founder acted in good faith, never meant to commit fraud or steal and basically got in over his head.",
    "span": [
      6198,
      6560
    ]
  }
]
```
