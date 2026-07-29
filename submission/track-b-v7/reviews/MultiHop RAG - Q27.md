# MultiHop RAG - Q27

**Question ID:** `Q-MH-027`

**Question:** Which company recently underwent a leadership strategy allowing Ryan Petersen to focus more on customer relations, faced workforce reductions by the same individual, and had its internal affairs publicly described as "deeply concerning" by Dave Clark, as reported by Cnbc | World Business News Leader and TechCrunch?

- category: `multi_hop_traversal`
- answer type: `entity`
- confidence: `0.9`
- confidence basis: `model_synthesis_bounded_to_oracle_retrieved_public_passages`
- latency: `37452 ms`
- truncated: `None`
- reasoning trace: `T-MH-027`

## Answer

Flexport

## Answer support

- `mh_e_f278b8c1ce031909c037`
- `mh_e_db9f021dc72eb5dc8012`
- `mh_e_29382f4c62831b109072`
- `mh_n_chunk_6683eecdd770d380da86`
- `mh_n_chunk_69789ffb0cb56c424b9c`
- `mh_n_chunk_7442e8fd3479455d3a0d`

## Reasoning and evidence path

### 1. `firewall_check`

Status: **allowed**; executed before planner: `None`.

### 2. `bounded_search_expansion`

```json
{
  "error": null,
  "operation": "bounded_search_expansion",
  "search_terms": [
    "Ryan Petersen",
    "Dave Clark",
    "Flexport",
    "CNBC",
    "TechCrunch",
    "Flexport leadership",
    "Ryan Petersen customer relations",
    "Dave Clark deeply concerning",
    "Flexport workforce reductions"
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
        "c0_0": "recently",
        "c0_1": "underwent",
        "c0_10": "publicly",
        "c0_11": "described",
        "c0_12": "deeply",
        "c0_13": "concerning",
        "c0_14": "dave",
        "c0_15": "clark",
        "c0_2": "leadership",
        "c0_3": "strategy",
        "c0_4": "allowing",
        "c0_5": "ryan",
        "c0_6": "petersen",
        "c0_7": "focus",
        "c0_8": "internal",
        "c0_9": "affairs",
        "limit": 300,
        "s0": "deeply concerning",
        "s1": "cnbc | world business news leader",
        "s2": "techcrunch",
        "seed_limit": 30,
        "t0": "recently",
        "t1": "underwent",
        "t10": "relations",
        "t11": "faced",
        "t12": "publicly",
        "t13": "described",
        "t14": "deeply",
        "t15": "concerning",
        "t16": "dave",
        "t17": "clark",
        "t18": "cnbc",
        "t19": "world",
        "t2": "leadership",
        "t20": "business",
        "t21": "news",
        "t22": "leader",
        "t23": "techcrunch",
        "t3": "strategy",
        "t4": "allowing",
        "t5": "ryan",
        "t6": "petersen",
        "t7": "focus",
        "t8": "more",
        "t9": "customer"
      },
      "chunk_count": 20,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t12) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t13) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t14) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t15) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t16) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t17) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t18) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t19) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t20) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t21) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t22) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t23) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23) > 0 THEN 8 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_2) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_2) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_3) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_3) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_4) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_4) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_5) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_5) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_6) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_6) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_7) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_7) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_8) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_8) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_9) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_9) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_10) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_10) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_11) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_11) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_12) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_12) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_13) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_13) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_14) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_14) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_15) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_15) > 0 THEN 6 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t12),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t13),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t14),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t15),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t16),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t17),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t18),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t19),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t20),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t21),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t22),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t23),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
    },
    {
      "binds": {
        "c0_0": "recently",
        "c0_1": "underwent",
        "c0_10": "publicly",
        "c0_11": "described",
        "c0_12": "deeply",
        "c0_13": "concerning",
        "c0_14": "dave",
        "c0_15": "clark",
        "c0_2": "leadership",
        "c0_3": "strategy",
        "c0_4": "allowing",
        "c0_5": "ryan",
        "c0_6": "petersen",
        "c0_7": "focus",
        "c0_8": "internal",
        "c0_9": "affairs",
        "limit": 300,
        "s0": "deeply concerning",
        "s1": "cnbc | world business news leader",
        "s2": "techcrunch",
        "seed_limit": 30,
        "t0": "ryan",
        "t1": "petersen",
        "t10": "workforce",
        "t11": "reductions",
        "t12": "recently",
        "t13": "underwent",
        "t14": "leadership",
        "t15": "strategy",
        "t16": "allowing",
        "t17": "focus",
        "t18": "more",
        "t19": "faced",
        "t2": "dave",
        "t20": "publicly",
        "t21": "described",
        "t22": "world",
        "t23": "business",
        "t24": "news",
        "t25": "leader",
        "t26": "techcrunch",
        "t3": "clark",
        "t4": "flexport",
        "t5": "cnbc",
        "t6": "customer",
        "t7": "relations",
        "t8": "deeply",
        "t9": "concerning"
      },
      "chunk_count": 30,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 52 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 26 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 60 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 30 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 52 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 26 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 54 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 27 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 60 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 30 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 52 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 26 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 60 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 30 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 62 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 31 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 56 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 28 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 64 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 32 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 62 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 31 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 64 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 32 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t12) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t13) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t14) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t15) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t16) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t17) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t18) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t19) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t20) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t21) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t22) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t23) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t24) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t24) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t25) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t25) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t26) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t26) > 0 THEN 8 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_2) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_2) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_3) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_3) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_4) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_4) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_5) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_5) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_6) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_6) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_7) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_7) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_8) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_8) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_9) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_9) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_10) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_10) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_11) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_11) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_12) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_12) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_13) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_13) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_14) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_14) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_15) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_15) > 0 THEN 6 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t12),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t13),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t14),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t15),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t16),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t17),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t18),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t19),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t20),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t21),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t22),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t23),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t24),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t24)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t25),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t25)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t26),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t26)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
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
  "edge_id": "mh_e_f278b8c1ce031909c037",
  "evidence": {
    "doc_id": "mh_doc_98b0ddf644244043e471",
    "page": 1,
    "span": [
      140,
      4000
    ]
  },
  "from": "mh_n_doc_98b0ddf644244043e471",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_6683eecdd770d380da86"
}
```

### 5. `edge_traversal`

```json
{
  "edge_id": "mh_e_db9f021dc72eb5dc8012",
  "evidence": {
    "doc_id": "mh_doc_98b0ddf644244043e471",
    "page": 1,
    "span": [
      8678,
      11254
    ]
  },
  "from": "mh_n_doc_98b0ddf644244043e471",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_69789ffb0cb56c424b9c"
}
```

### 6. `edge_traversal`

```json
{
  "edge_id": "mh_e_29382f4c62831b109072",
  "evidence": {
    "doc_id": "mh_doc_f30e2f731a65307056c5",
    "page": 1,
    "span": [
      3920,
      4188
    ]
  },
  "from": "mh_n_doc_f30e2f731a65307056c5",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_7442e8fd3479455d3a0d"
}
```

### 7. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_6683eecdd770d380da86"
  ],
  "claim": "Ryan Petersen ousted Dave Clark to resume CEO role at Flexport and focus on operations/customer strategy after Clark's tenure",
  "operation": "evidence_synthesis"
}
```

### 8. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_6683eecdd770d380da86",
    "mh_n_chunk_69789ffb0cb56c424b9c"
  ],
  "claim": "Petersen publicly criticized Clark for secretly expanding headcount (implying subsequent workforce reductions) and other decisions at Flexport",
  "operation": "evidence_synthesis"
}
```

### 9. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_69789ffb0cb56c424b9c",
    "mh_n_chunk_7442e8fd3479455d3a0d"
  ],
  "claim": "Dave Clark's departure and Flexport's internal issues (including forecasts and leases) described in detail with Clark disputing claims; Flexport also referenced in TechCrunch layoffs/acquisition context",
  "operation": "evidence_synthesis"
}
```

### 10. `grounded_finalization`

```json
{
  "answer_derived_only_from_cited_chunks": true,
  "operation": "grounded_finalization"
}
```

## Graph elements used

### Nodes

- `mh_n_doc_98b0ddf644244043e471`
- `mh_n_chunk_6683eecdd770d380da86`
- `mh_n_chunk_69789ffb0cb56c424b9c`
- `mh_n_doc_f30e2f731a65307056c5`
- `mh_n_chunk_7442e8fd3479455d3a0d`

### Edges

- `mh_e_f278b8c1ce031909c037`
- `mh_e_db9f021dc72eb5dc8012`
- `mh_e_29382f4c62831b109072`

## Citations

```json
[
  {
    "doc_id": "mh_doc_98b0ddf644244043e471",
    "node_id": "mh_n_chunk_6683eecdd770d380da86",
    "page": 1,
    "span": [
      140,
      4000
    ]
  },
  {
    "doc_id": "mh_doc_98b0ddf644244043e471",
    "node_id": "mh_n_chunk_69789ffb0cb56c424b9c",
    "page": 1,
    "span": [
      8678,
      11254
    ]
  },
  {
    "doc_id": "mh_doc_f30e2f731a65307056c5",
    "node_id": "mh_n_chunk_7442e8fd3479455d3a0d",
    "page": 1,
    "span": [
      3920,
      4188
    ]
  }
]
```

## Retrieved context

```json
[
  {
    "doc_id": "mh_doc_98b0ddf644244043e471",
    "node_id": "mh_n_chunk_6683eecdd770d380da86",
    "page": 1,
    "snippet": "On Sept. 13, Flexport founder Ryan Petersen took the stage at North America's premier supply chain conference in Phoenix. It was exactly a week after he'd forced out his hand-picked successor as CEO, ex-Amazon executive Dave Clark, so Petersen could once again run the show. Sitting in the first few rows of attendees was Clark, the man he'd ousted just a year into the job. Petersen was surprised that he showed up, according to people with knowledge of the matter. Days earlier, Petersen had excoriated Clark, alleging he'd secretly expanded the company's headcount and taken on unnecessary leases without Petersen or the board's knowledge. On X, formerly known as Twitter, Petersen wrote, \"Strategic Plan, Day 1: Make better decisions!\" With Clark sitting a few feet away, Petersen struck a different tone. \"I think we're going to look back and go, 'Wow I'd probably do that all over again because of the progress that we've made,'\" Petersen said, in an interview on stage. Doing it over again would seem to suggest hiring Clark wasn't a bad decision. Petersen went even further, personally commending Clark for orchestrating the $1.3 billion purchase of Deliverr from Shopify , picking up supply chain technology for last-mile deliveries. That deal was announced in May. \"I'm very, very lucky because I wouldn't have had the courage to go and do that acquisition, but I give all the credit in the world to Dave Clark,\" Petersen said. \"There's no one probably in the world who would be better at running that last-mile e-com fulfillment network. Personally, I don't have any experience and I would've been pretty intimidated to try and go pull that off.\" The mixed messaging from the 43-year-old Flexport founder underscores the dysfunction surrounding the sudden firing of Clark, who previously spent 23 years at Amazon and built its mammoth logistics network on the way to becoming one of Jeff Bezos' top deputies. It's also indicative of a bigger challenge facing Flexport, whose software is designed to simplify the process of transporting goods. The company was valued at $8 billion by private investors in early 2022, just as the economy was turning and the 10-year tech bull market was coming to an end. As a high-valued company backed by powerful VCs, Flexport has been trying to simultaneously operate in Silicon Valley startup growth mode while also restraining expenses to reflect the new economic realities and to cope with supply chain bottlenecks. This account is based on conversations with people close to Clark and Petersen. They requested anonymity to discuss confidential interactions. Their perspectives have been corroborated by internal documents and communications reviewed by CNBC. Petersen has publicly said Clark overspent, overhired and overpromised, something his allies echoed to CNBC. He burned through cash and kept Petersen in the dark about key financials and an ambitious expansion into providing end-to-end supply chain tools for small and medium-sized businesses. People close to Petersen pointed to a number of previously unreported incidents that eroded his confidence in Clark. But documents viewed by CNBC and sources close to Clark undermine those claims. They show that Clark, who arrived when the company was struggling to bill customers and track containers, worked closely with the board and Petersen to implement decisions that Flexport now suggests were ill-advised. Evidence to support Flexport's claims of financial mismanagement is lacking, raising questions about whether that narrative was put forward to justify Clark's exit. A Flexport spokesperson rejected that characterization. \"Ryan Petersen returned as CEO in order to restore Flexport's culture of customer engagement, and drive the growth and cost discipline required to return the company to profitability,\" the spokesperson said in a statement.",
    "span": [
      140,
      4000
    ]
  },
  {
    "doc_id": "mh_doc_98b0ddf644244043e471",
    "node_id": "mh_n_chunk_69789ffb0cb56c424b9c",
    "page": 1,
    "snippet": "For much of the summer, Clark had pushed then-CFO Kenny Wagers and his financial planning and analysis team to realign Flexport's year-end and 18-month forecasts, according to a person close to the situation. The reasons were obvious. At the beginning of 2022, it cost around $14,500 to move a single container across the Pacific. By late 2022, prices of ocean freight from Asia to the U.S. West Coast were down 90% from a year earlier, due largely to weakening global demand. Because Flexport makes money by charging fees for the transportation of goods, the company's business was getting hammered. But Wagers and Stuart Leung, a Flexport finance executive and a close Petersen ally, were reluctant to pare back forecasts, frustrating Clark, who felt those projections were overly optimistic. Wagers and Leung did not respond to CNBC's interview requests. Clark ultimately prevailed, but the revised forecasts distressed Petersen. Clark, Petersen and Wagers met in Texas in mid-August to fine-tune the forecasts. A source close to Petersen told CNBC that the meeting went poorly for Clark because a so-called whistleblower \u2014 identified as a senior finance executive \u2014 stepped forward shortly before it began and told Petersen that the numbers being presented were \"not real.\" The source referred to the senior finance executive as a whistleblower because of the information he disclosed to Petersen about Clark. Documents seen by CNBC and conversations with people with direct knowledge of the board meeting make it clear that there were no substantiated whistleblower actions or allegations of financial impropriety. Flexport's spokesperson told CNBC in a statement: \"There was no whistleblower nor was there any financial misconduct. Any allegations to the contrary are completely false.\" On Sept. 15, shortly after CNBC spoke with the Petersen source, legal counsel for Clark sent a cease-and-desist letter to Flexport. The letter, viewed by CNBC, instructed the company to preserve and retain all communications involving Clark's departure. The letter disputes the existence of a whistleblower and lists specific allegations as false and defamatory, including Petersen's claims that Clark was an unfit CEO because he overextended the company's lease obligations. Five hours after the letter was sent, the source close to Petersen contacted CNBC and asked to retract their statements and all details related to Clark's firing or about the so-called whistleblower. CNBC declined to retract his statements. Petersen has since deleted several of his posts criticizing Clark.",
    "span": [
      8678,
      11254
    ]
  },
  {
    "doc_id": "mh_doc_f30e2f731a65307056c5",
    "node_id": "mh_n_chunk_7442e8fd3479455d3a0d",
    "page": 1,
    "snippet": "Flexport is in talks to acquire the technology of Convoy, the once buzzy digital freight startup that abruptly shuttered after failing to find a buyer. This possible deal, which was reported by WSJ, didn\u2019t have any other details, but it still made me raise an eyebrow.",
    "span": [
      3920,
      4188
    ]
  }
]
```
