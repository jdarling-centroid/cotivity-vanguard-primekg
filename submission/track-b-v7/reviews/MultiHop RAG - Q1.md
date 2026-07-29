# MultiHop RAG - Q1

**Question ID:** `Q-MH-001`

**Question:** What is the name of the platform that is scrutinized for serving content related to eating disorders, as reported by 'The Age', and is also recognized for its strategic focus on music-related services aiming to integrate with the music industry, according to 'Music Business Worldwide'?

- category: `multi_hop_traversal`
- answer type: `entity`
- confidence: `0.9`
- confidence basis: `model_synthesis_bounded_to_oracle_retrieved_public_passages`
- latency: `9528 ms`
- truncated: `None`
- reasoning trace: `T-MH-001`

## Answer

TikTok

## Answer support

- `mh_e_dc0c8a17804abc78fb6a`
- `mh_e_5ba4ce3c3efe023d77a2`
- `mh_n_chunk_a097b96baa0e24642821`
- `mh_n_chunk_f12127774553db08cb43`

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
        "c0_0": "scrutinized",
        "c0_1": "serving",
        "c0_2": "content",
        "c0_3": "related",
        "c0_4": "eating",
        "c0_5": "disorders",
        "c1_0": "recognized",
        "c1_1": "strategic",
        "c1_2": "focus",
        "c1_3": "music-related",
        "c1_4": "services",
        "c1_5": "aiming",
        "c1_6": "integrate",
        "c1_7": "music",
        "c1_8": "industry",
        "limit": 300,
        "s0": "the age",
        "s1": "music business worldwide",
        "s2": "business world",
        "seed_limit": 30,
        "t0": "platform",
        "t1": "scrutinized",
        "t10": "focus",
        "t11": "music-related",
        "t12": "services",
        "t13": "aiming",
        "t14": "integrate",
        "t15": "music",
        "t16": "industry",
        "t17": "business",
        "t18": "worldwide",
        "t2": "serving",
        "t3": "content",
        "t4": "related",
        "t5": "eating",
        "t6": "disorders",
        "t7": "age",
        "t8": "recognized",
        "t9": "strategic"
      },
      "chunk_count": 20,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 18 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 9 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t12) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t13) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t14) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t15) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t16) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t17) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t18) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18) > 0 THEN 7 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 36 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 18 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_2) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_2) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_3) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_3) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_4) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_4) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_5) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_5) > 0 THEN 14 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c1_0) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_0) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_1) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_1) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_2) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_2) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_3) > 0 THEN 40 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_3) > 0 THEN 20 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_4) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_4) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_5) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_5) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_6) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_6) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_7) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_7) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_8) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_8) > 0 THEN 12 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t12),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t13),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t14),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t15),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t16),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t17),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t18),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
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
  "edge_id": "mh_e_dc0c8a17804abc78fb6a",
  "evidence": {
    "doc_id": "mh_doc_e74348af72598e400e69",
    "page": 1,
    "span": [
      5430,
      6940
    ]
  },
  "from": "mh_n_doc_e74348af72598e400e69",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_a097b96baa0e24642821"
}
```

### 5. `edge_traversal`

```json
{
  "edge_id": "mh_e_5ba4ce3c3efe023d77a2",
  "evidence": {
    "doc_id": "mh_doc_1c479a72755b48720130",
    "page": 1,
    "span": [
      5957,
      6174
    ]
  },
  "from": "mh_n_doc_1c479a72755b48720130",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_f12127774553db08cb43"
}
```

### 6. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_a097b96baa0e24642821"
  ],
  "claim": "TikTok is serving eating-disorder content to those already struggling (The Age)",
  "operation": "evidence_synthesis"
}
```

### 7. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_f12127774553db08cb43"
  ],
  "claim": "TikTok has focused so heavily on developing music-related services... plans to reinvent itself as a part of the music industry (Music Business Worldwide)",
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

- `mh_n_doc_e74348af72598e400e69`
- `mh_n_chunk_a097b96baa0e24642821`
- `mh_n_doc_1c479a72755b48720130`
- `mh_n_chunk_f12127774553db08cb43`

### Edges

- `mh_e_dc0c8a17804abc78fb6a`
- `mh_e_5ba4ce3c3efe023d77a2`

## Citations

```json
[
  {
    "doc_id": "mh_doc_e74348af72598e400e69",
    "node_id": "mh_n_chunk_a097b96baa0e24642821",
    "page": 1,
    "span": [
      5430,
      6940
    ]
  },
  {
    "doc_id": "mh_doc_1c479a72755b48720130",
    "node_id": "mh_n_chunk_f12127774553db08cb43",
    "page": 1,
    "span": [
      5957,
      6174
    ]
  }
]
```

## Retrieved context

```json
[
  {
    "doc_id": "mh_doc_e74348af72598e400e69",
    "node_id": "mh_n_chunk_a097b96baa0e24642821",
    "page": 1,
    "snippet": "\u201cWe wrote it when we were so young,\u201d reflects Andrews. \u201cWe truly had internalised this belief that for our words to be worthy of attention, they had to mine the deepest, darkest events that have ever happened to us.\u201d This feeling is one Andrews has spoken about before, referring to an essay she wrote for the book which included details of her sexual assault. \u201cI wish I\u2019d just saved that for myself,\u201d she says, adding that while she wouldn\u2019t take back the essay, she would take back some of the details. Zara McDonald wears Luuda shirt, $390, and shorts, $290. Converse shoes, $130, from Hype DC. Credit: Hugh Stewart Says McDonald, \u201cIf I was to psychoanalyse us, I\u2019d say we felt guilty for having that platform that young.\u201d But that imposter syndrome is nowhere to be seen in 4am, in which Andrews and McDonald are happy to take their rightful place as agony aunts to young Australian women. In it, readers trust Andrews, McDonald and other Shameless columnists with their quandaries on everything from infidelity to sibling rivalry. The book comes at a time when many young women have trust issues. TikTok is serving eating-disorder content to those already struggling, influencers and celebrities post undisclosed advertisements, and algorithms work to push everything from egg-freezing to injectables. Everywhere young women look, someone is making money off them. Zara McDonald (left) wears Venroy mini dress, $200. Michelle Andrews (right) wears Venroy shirt, $280, and pants, $280. Credit: Hugh Stewart",
    "span": [
      5430,
      6940
    ]
  },
  {
    "doc_id": "mh_doc_1c479a72755b48720130",
    "node_id": "mh_n_chunk_f12127774553db08cb43",
    "page": 1,
    "snippet": "The data clearly shows why TikTok has focused so heavily on developing music-related services, to the point that one could be forgiven for thinking the company plans to reinvent itself as a part of the music industry.",
    "span": [
      5957,
      6174
    ]
  }
]
```
