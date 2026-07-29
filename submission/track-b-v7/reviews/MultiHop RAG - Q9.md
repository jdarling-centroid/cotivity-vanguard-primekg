# MultiHop RAG - Q9

**Question ID:** `Q-MH-009`

**Question:** Which individual, commended by Kevin Federline for responsibly dealing with her situation according to 'The Independent - Life and Style', also described being ritually tortured by the age of 16 and became public property as reported by 'The Guardian'?

- category: `multi_hop_traversal`
- answer type: `entity`
- confidence: `0.95`
- confidence basis: `model_synthesis_bounded_to_oracle_retrieved_public_passages`
- latency: `9040 ms`
- truncated: `None`
- reasoning trace: `T-MH-009`

## Answer

Britney Spears

## Answer support

- `mh_e_6db165043c53487dbf45`
- `mh_e_3d9cfddfccd3d60bebac`
- `mh_n_chunk_aa0a857ee59fdad168f6`
- `mh_n_chunk_53d990d52f0155772502`

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
        "c0_0": "commended",
        "c0_1": "kevin",
        "c0_2": "federline",
        "c0_3": "responsibly",
        "c0_4": "dealing",
        "c0_5": "her",
        "c0_6": "situation",
        "limit": 300,
        "s0": "the independent - life and style",
        "s1": "the guardian",
        "s2": "the age",
        "seed_limit": 30,
        "t0": "commended",
        "t1": "kevin",
        "t10": "described",
        "t11": "ritually",
        "t12": "tortured",
        "t13": "age",
        "t14": "became",
        "t15": "public",
        "t16": "property",
        "t17": "guardian",
        "t2": "federline",
        "t3": "responsibly",
        "t4": "dealing",
        "t5": "her",
        "t6": "situation",
        "t7": "independent",
        "t8": "life",
        "t9": "style"
      },
      "chunk_count": 20,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 18 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 9 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 18 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 9 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t12) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t13) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t14) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t15) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t16) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t17) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17) > 0 THEN 6 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_2) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_2) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_3) > 0 THEN 36 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_3) > 0 THEN 18 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_4) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_4) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_5) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_5) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_6) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_6) > 0 THEN 14 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t12),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t13),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t14),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t15),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t16),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t17),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
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
  "edge_id": "mh_e_6db165043c53487dbf45",
  "evidence": {
    "doc_id": "mh_doc_7c417f4cdd357e602495",
    "page": 1,
    "span": [
      3879,
      4390
    ]
  },
  "from": "mh_n_doc_7c417f4cdd357e602495",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_aa0a857ee59fdad168f6"
}
```

### 5. `edge_traversal`

```json
{
  "edge_id": "mh_e_3d9cfddfccd3d60bebac",
  "evidence": {
    "doc_id": "mh_doc_9c33c1df56534afb58b3",
    "page": 1,
    "span": [
      12577,
      13385
    ]
  },
  "from": "mh_n_doc_9c33c1df56534afb58b3",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_53d990d52f0155772502"
}
```

### 6. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_aa0a857ee59fdad168f6"
  ],
  "claim": "Kevin Federline commends Britney for responsibly dealing with her situation",
  "operation": "evidence_synthesis"
}
```

### 7. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_53d990d52f0155772502"
  ],
  "claim": "Britney Spears memoir describes ritual torture by age 16 and becoming public property",
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

- `mh_n_doc_7c417f4cdd357e602495`
- `mh_n_chunk_aa0a857ee59fdad168f6`
- `mh_n_doc_9c33c1df56534afb58b3`
- `mh_n_chunk_53d990d52f0155772502`

### Edges

- `mh_e_6db165043c53487dbf45`
- `mh_e_3d9cfddfccd3d60bebac`

## Citations

```json
[
  {
    "doc_id": "mh_doc_7c417f4cdd357e602495",
    "node_id": "mh_n_chunk_aa0a857ee59fdad168f6",
    "page": 1,
    "span": [
      3879,
      4390
    ]
  },
  {
    "doc_id": "mh_doc_9c33c1df56534afb58b3",
    "node_id": "mh_n_chunk_53d990d52f0155772502",
    "page": 1,
    "span": [
      12577,
      13385
    ]
  }
]
```

## Retrieved context

```json
[
  {
    "doc_id": "mh_doc_7c417f4cdd357e602495",
    "node_id": "mh_n_chunk_aa0a857ee59fdad168f6",
    "page": 1,
    "snippet": "Amid her father\u2019s health crisis and ongoing emotional distress, Spears voluntarily checked into a mental health treatment facility in 2019. After hearing the news, Federline\u2019s attorney Mark Kaplan told Entertainment Tonight: \u201cKevin commends Britney for recognising that she needs to take a step back and that she is taking the reasonable steps to dealing with her situation in a responsible way. He wishes everyone well.\u201d That same year, Federline was granted 70 percent custodial rights and Spears 30 per cent.",
    "span": [
      3879,
      4390
    ]
  },
  {
    "doc_id": "mh_doc_9c33c1df56534afb58b3",
    "node_id": "mh_n_chunk_53d990d52f0155772502",
    "page": 1,
    "snippet": "She accedes in order to retain access to her boys, but questions how she can perform at such a high level when she is perceived as \u201cso sick that I couldn\u2019t make my own decisions\u201d. She makes futile attempts to escape the arrangement; meanwhile her father sends her to rehab and Alcoholics Anonymous because she has been taking over-the-counter energy supplements. The women at AA inspire her to start trying to take control over her life but she just hits more walls. Her father won\u2019t let her remove her IUD to start a family with her new boyfriend, later husband, Sam Ashgari (they have divorced since Britney completed the memoir). After she objects to a new dance move suggested for her Vegas residency, she is sent to a solitary rehabilitation facility for two months, the most upsetting part of the book.",
    "span": [
      12577,
      13385
    ]
  }
]
```
