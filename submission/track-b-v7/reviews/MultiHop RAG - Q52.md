# MultiHop RAG - Q52

**Question ID:** `Q-MH-052`

**Question:** What is the first letter of the name of the company that, according to an article from The Financial Times, received the most European patents in 2021, and is also mentioned in a Bloomberg article as having faced a significant legal challenge at the European Patent Office over one of its key patents?

- category: `multi_hop_traversal`
- answer type: `short_text`
- confidence: `0.0`
- confidence basis: `model_synthesis_bounded_to_oracle_retrieved_public_passages`
- latency: `32992 ms`
- truncated: `None`
- reasoning trace: `T-MH-052`

## Answer

Insufficient evidence in the retrieved MultiHopRAG graph.

## Answer support

- `mh_e_da122bd165d4b216052a`
- `mh_e_9f87cbbedfa5910c6f49`
- `mh_n_chunk_4990e63e1a4e7671b182`
- `mh_n_chunk_04e7fd366f1095bec326`

## Reasoning and evidence path

### 1. `firewall_check`

Status: **allowed**; executed before planner: `None`.

### 2. `bounded_search_expansion`

```json
{
  "error": null,
  "operation": "bounded_search_expansion",
  "search_terms": [
    "Huawei",
    "Samsung",
    "LG Electronics",
    "Siemens",
    "Qualcomm",
    "Ericsson",
    "European patents 2021",
    "EPO legal challenge",
    "Financial Times patents ranking"
  ]
}
```

### 3. `oracle_graph_retrieval`

```json
{
  "operation": "oracle_graph_retrieval",
  "queries": [
    {
      "binds": {
        "c0_0": "first",
        "c0_1": "letter",
        "c1_0": "mentioned",
        "c1_1": "bloomberg",
        "c1_10": "office",
        "c1_11": "over",
        "c1_12": "one",
        "c1_13": "key",
        "c1_14": "patents",
        "c1_2": "article",
        "c1_3": "having",
        "c1_4": "faced",
        "c1_5": "significant",
        "c1_6": "legal",
        "c1_7": "challenge",
        "c1_8": "european",
        "c1_9": "patent",
        "limit": 300,
        "s0": "financial times",
        "seed_limit": 30,
        "t0": "first",
        "t1": "letter",
        "t10": "mentioned",
        "t11": "bloomberg",
        "t12": "having",
        "t13": "faced",
        "t14": "significant",
        "t15": "legal",
        "t16": "challenge",
        "t17": "patent",
        "t18": "office",
        "t19": "over",
        "t2": "article",
        "t20": "one",
        "t21": "key",
        "t3": "financial",
        "t4": "times",
        "t5": "received",
        "t6": "most",
        "t7": "european",
        "t8": "patents",
        "t9": "2021"
      },
      "chunk_count": 20,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t12) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t13) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t14) > 0 THEN 18 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14) > 0 THEN 9 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t15) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t16) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t17) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t18) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t19) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t20) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t21) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21) > 0 THEN 1 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 8 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c1_0) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_0) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_1) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_1) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_2) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_2) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_3) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_3) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_4) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_4) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_5) > 0 THEN 36 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_5) > 0 THEN 18 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_6) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_6) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_7) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_7) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_8) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_8) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_9) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_9) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_10) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_10) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_11) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_11) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_12) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_12) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_13) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_13) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_14) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_14) > 0 THEN 10 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t12),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t13),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t14),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t15),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t16),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t17),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t18),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t19),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t20),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t21),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
    },
    {
      "binds": {
        "c0_0": "first",
        "c0_1": "letter",
        "c1_0": "mentioned",
        "c1_1": "bloomberg",
        "c1_10": "office",
        "c1_11": "over",
        "c1_12": "one",
        "c1_13": "key",
        "c1_14": "patents",
        "c1_2": "article",
        "c1_3": "having",
        "c1_4": "faced",
        "c1_5": "significant",
        "c1_6": "legal",
        "c1_7": "challenge",
        "c1_8": "european",
        "c1_9": "patent",
        "limit": 300,
        "s0": "financial times",
        "seed_limit": 30,
        "t0": "huawei",
        "t1": "samsung",
        "t10": "times",
        "t11": "ranking",
        "t12": "first",
        "t13": "letter",
        "t14": "article",
        "t15": "received",
        "t16": "most",
        "t17": "european",
        "t18": "patents",
        "t19": "2021",
        "t2": "electronics",
        "t20": "mentioned",
        "t21": "bloomberg",
        "t22": "having",
        "t23": "faced",
        "t24": "significant",
        "t25": "patent",
        "t26": "office",
        "t27": "over",
        "t28": "one",
        "t29": "key",
        "t3": "siemens",
        "t4": "qualcomm",
        "t5": "ericsson",
        "t6": "epo",
        "t7": "legal",
        "t8": "challenge",
        "t9": "financial"
      },
      "chunk_count": 30,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 56 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 28 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 58 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 29 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 66 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 33 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 58 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 29 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 60 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 30 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 60 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 30 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 50 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 25 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 54 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 27 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 62 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 31 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 62 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 31 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 54 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 27 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 58 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 29 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t12) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t13) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t14) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t15) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t16) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t17) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t18) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t19) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t20) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t21) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t22) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t23) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t24) > 0 THEN 18 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t24) > 0 THEN 9 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t25) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t25) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t26) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t26) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t27) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t27) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t28) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t28) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t29) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t29) > 0 THEN 1 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 8 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c1_0) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_0) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_1) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_1) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_2) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_2) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_3) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_3) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_4) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_4) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_5) > 0 THEN 36 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_5) > 0 THEN 18 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_6) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_6) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_7) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_7) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_8) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_8) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_9) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_9) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_10) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_10) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_11) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_11) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_12) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_12) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_13) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_13) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_14) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_14) > 0 THEN 10 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t12),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t13),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t14),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t15),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t16),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t17),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t18),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t19),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t20),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t21),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t22),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t23),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t24),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t24)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t25),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t25)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t26),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t26)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t27),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t27)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t28),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t28)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t29),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t29)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
    }
  ],
  "query_count": 2,
  "read_only": true,
  "retrieved_chunk_count": 50
}
```

### 4. `edge_traversal`

```json
{
  "edge_id": "mh_e_da122bd165d4b216052a",
  "evidence": {
    "doc_id": "mh_doc_4ee42628c03e6155faf4",
    "page": 1,
    "span": [
      3389,
      3884
    ]
  },
  "from": "mh_n_doc_4ee42628c03e6155faf4",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_4990e63e1a4e7671b182"
}
```

### 5. `edge_traversal`

```json
{
  "edge_id": "mh_e_9f87cbbedfa5910c6f49",
  "evidence": {
    "doc_id": "mh_doc_4ee42628c03e6155faf4",
    "page": 1,
    "span": [
      5717,
      6051
    ]
  },
  "from": "mh_n_doc_4ee42628c03e6155faf4",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_04e7fd366f1095bec326"
}
```

### 6. `grounded_finalization`

```json
{
  "answer_derived_only_from_cited_chunks": true,
  "operation": "grounded_finalization"
}
```

## Graph elements used

### Nodes

- `mh_n_doc_4ee42628c03e6155faf4`
- `mh_n_chunk_4990e63e1a4e7671b182`
- `mh_n_chunk_04e7fd366f1095bec326`

### Edges

- `mh_e_da122bd165d4b216052a`
- `mh_e_9f87cbbedfa5910c6f49`

## Citations

```json
[
  {
    "doc_id": "mh_doc_4ee42628c03e6155faf4",
    "node_id": "mh_n_chunk_4990e63e1a4e7671b182",
    "page": 1,
    "span": [
      3389,
      3884
    ]
  },
  {
    "doc_id": "mh_doc_4ee42628c03e6155faf4",
    "node_id": "mh_n_chunk_04e7fd366f1095bec326",
    "page": 1,
    "span": [
      5717,
      6051
    ]
  }
]
```

## Retrieved context

```json
[
  {
    "doc_id": "mh_doc_4ee42628c03e6155faf4",
    "node_id": "mh_n_chunk_4990e63e1a4e7671b182",
    "page": 1,
    "snippet": "One of the most significant changes, say asset managers, is the fundamental shift in the way global funds now look at China. The geopolitics of US-China tensions, chip wars, decoupling and \u201cfriendshoring\u201d seem, in particular, to be working significantly in Japan\u2019s favour. Asia-focused global investment is rotating out of China and into Tokyo stocks, real estate and other assets, just as large parts of corporate Japan are engaging more actively with shareholders than at any time in the past.",
    "span": [
      3389,
      3884
    ]
  },
  {
    "doc_id": "mh_doc_4ee42628c03e6155faf4",
    "node_id": "mh_n_chunk_04e7fd366f1095bec326",
    "page": 1,
    "snippet": "Efforts by Japanese businesses to demonstrate better governance are aided by government initiatives to make Tokyo more attractive for foreign asset managers. Kishida has promised major reform of the country\u2019s $5tn asset management industry, which would ease regulations that had made it difficult for foreign and new players to enter.",
    "span": [
      5717,
      6051
    ]
  }
]
```
