# MultiHop RAG - Q21

**Question ID:** `Q-MH-021`

**Question:** Who, according to reports from 'Essentially Sports' and 'Sporting News,' has accumulated a net worth of $180 million by 2023 and attributes a recent boxing victory to altering a punch, while also engaging in increasingly lucrative fights over the years?

- category: `multi_hop_traversal`
- answer type: `entity`
- confidence: `0.7`
- confidence basis: `model_synthesis_bounded_to_oracle_retrieved_public_passages`
- latency: `39727 ms`
- truncated: `None`
- reasoning trace: `T-MH-021`

## Answer

Canelo Alvarez

## Answer support

- `mh_e_ff82248bbc674b43add3`
- `mh_e_5604f1fd3b47b657a5e8`
- `mh_n_chunk_407cfbb4057c581ff947`
- `mh_n_chunk_0370236f0a9af43c7bf3`

## Reasoning and evidence path

### 1. `firewall_check`

Status: **allowed**; executed before planner: `None`.

### 2. `bounded_search_expansion`

```json
{
  "error": null,
  "operation": "bounded_search_expansion",
  "search_terms": [
    "Canelo \u00c1lvarez",
    "Floyd Mayweather",
    "Manny Pacquiao",
    "Tyson Fury",
    "Anthony Joshua",
    "Ryan Garcia",
    "net worth $180 million 2023",
    "altering a punch boxing",
    "Essentially Sports Sporting News"
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
        "c0_0": "accumulated",
        "c0_1": "net",
        "c0_10": "engaging",
        "c0_11": "increasingly",
        "c0_12": "lucrative",
        "c0_13": "fights",
        "c0_14": "over",
        "c0_15": "years",
        "c0_2": "worth",
        "c0_3": "180",
        "c0_4": "million",
        "c0_5": "2023",
        "c0_6": "attributes",
        "c0_7": "recent",
        "c0_8": "altering",
        "c0_9": "punch",
        "limit": 300,
        "s0": "essentially sports",
        "s1": "sporting news,",
        "s2": "sporting news",
        "seed_limit": 30,
        "t0": "essentially",
        "t1": "sports",
        "t10": "attributes",
        "t11": "recent",
        "t12": "boxing",
        "t13": "victory",
        "t14": "altering",
        "t15": "punch",
        "t16": "engaging",
        "t17": "increasingly",
        "t18": "lucrative",
        "t19": "fights",
        "t2": "sporting",
        "t20": "over",
        "t21": "years",
        "t3": "news",
        "t4": "accumulated",
        "t5": "net",
        "t6": "worth",
        "t7": "180",
        "t8": "million",
        "t9": "2023"
      },
      "chunk_count": 20,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 18 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 9 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 18 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 9 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t12) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t13) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t14) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t15) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t16) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t17) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t18) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t19) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t20) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t21) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21) > 0 THEN 3 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 36 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 18 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_2) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_2) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_3) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_3) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_4) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_4) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_5) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_5) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_6) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_6) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_7) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_7) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_8) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_8) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_9) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_9) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_10) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_10) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_11) > 0 THEN 40 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_11) > 0 THEN 20 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_12) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_12) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_13) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_13) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_14) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_14) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_15) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_15) > 0 THEN 6 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t12),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t13),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t14),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t15),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t16),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t17),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t18),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t19),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t20),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t21),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
    },
    {
      "binds": {
        "c0_0": "accumulated",
        "c0_1": "net",
        "c0_10": "engaging",
        "c0_11": "increasingly",
        "c0_12": "lucrative",
        "c0_13": "fights",
        "c0_14": "over",
        "c0_15": "years",
        "c0_2": "worth",
        "c0_3": "180",
        "c0_4": "million",
        "c0_5": "2023",
        "c0_6": "attributes",
        "c0_7": "recent",
        "c0_8": "altering",
        "c0_9": "punch",
        "limit": 300,
        "s0": "essentially sports",
        "s1": "sporting news,",
        "s2": "sporting news",
        "seed_limit": 30,
        "t0": "canelo",
        "t1": "lvarez",
        "t10": "sporting",
        "t11": "news",
        "t12": "accumulated",
        "t13": "net",
        "t14": "worth",
        "t15": "180",
        "t16": "million",
        "t17": "2023",
        "t18": "attributes",
        "t19": "recent",
        "t2": "floyd",
        "t20": "victory",
        "t21": "altering",
        "t22": "engaging",
        "t23": "increasingly",
        "t24": "lucrative",
        "t25": "fights",
        "t26": "over",
        "t27": "years",
        "t3": "mayweather",
        "t4": "manny",
        "t5": "pacquiao",
        "t6": "punch",
        "t7": "boxing",
        "t8": "essentially",
        "t9": "sports"
      },
      "chunk_count": 30,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 56 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 28 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 56 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 28 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 54 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 27 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 64 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 32 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 54 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 27 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 60 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 30 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 54 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 27 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 56 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 28 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 66 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 33 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 56 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 28 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 60 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 30 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 52 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 26 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t12) > 0 THEN 18 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12) > 0 THEN 9 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t13) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t14) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t15) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t16) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t17) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t18) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t19) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t20) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t21) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t22) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t23) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t24) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t24) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t25) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t25) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t26) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t26) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t27) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t27) > 0 THEN 3 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 36 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 18 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_2) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_2) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_3) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_3) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_4) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_4) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_5) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_5) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_6) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_6) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_7) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_7) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_8) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_8) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_9) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_9) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_10) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_10) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_11) > 0 THEN 40 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_11) > 0 THEN 20 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_12) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_12) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_13) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_13) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_14) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_14) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_15) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_15) > 0 THEN 6 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t12),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t13),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t14),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t15),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t16),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t17),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t18),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t19),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t20),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t21),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t22),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t23),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t24),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t24)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t25),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t25)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t26),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t26)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t27),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t27)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
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
  "edge_id": "mh_e_ff82248bbc674b43add3",
  "evidence": {
    "doc_id": "mh_doc_f044cf63ebd544318694",
    "page": 1,
    "span": [
      3657,
      4184
    ]
  },
  "from": "mh_n_doc_f044cf63ebd544318694",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_407cfbb4057c581ff947"
}
```

### 5. `edge_traversal`

```json
{
  "edge_id": "mh_e_5604f1fd3b47b657a5e8",
  "evidence": {
    "doc_id": "mh_doc_dc17cfa263f250c17823",
    "page": 1,
    "span": [
      614,
      825
    ]
  },
  "from": "mh_n_doc_dc17cfa263f250c17823",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_0370236f0a9af43c7bf3"
}
```

### 6. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_407cfbb4057c581ff947"
  ],
  "claim": "Canelo engaged in increasingly profitable bouts over the years per Essentially Sports",
  "operation": "evidence_synthesis"
}
```

### 7. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_0370236f0a9af43c7bf3"
  ],
  "claim": "Canelo won recent 2023 boxing match vs Charlo per Sporting News",
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

- `mh_n_doc_f044cf63ebd544318694`
- `mh_n_chunk_407cfbb4057c581ff947`
- `mh_n_doc_dc17cfa263f250c17823`
- `mh_n_chunk_0370236f0a9af43c7bf3`

### Edges

- `mh_e_ff82248bbc674b43add3`
- `mh_e_5604f1fd3b47b657a5e8`

## Citations

```json
[
  {
    "doc_id": "mh_doc_f044cf63ebd544318694",
    "node_id": "mh_n_chunk_407cfbb4057c581ff947",
    "page": 1,
    "span": [
      3657,
      4184
    ]
  },
  {
    "doc_id": "mh_doc_dc17cfa263f250c17823",
    "node_id": "mh_n_chunk_0370236f0a9af43c7bf3",
    "page": 1,
    "span": [
      614,
      825
    ]
  }
]
```

## Retrieved context

```json
[
  {
    "doc_id": "mh_doc_f044cf63ebd544318694",
    "node_id": "mh_n_chunk_407cfbb4057c581ff947",
    "page": 1,
    "snippet": "If Canelo\u2019s PPV pull was ever in question, his history of fight purses should convince everyone. Stepping back in time, Canelo\u2019s fight with Mayweather collected 2.2 million pay-per-view buys. His 2017 bout against Julio C\u00e9sar Ch\u00e1vez Jr. collected 1 million PPV buys. Canelo\u2019s first battle with Gennady Golovkin gathered 1.3 million PPV sales. In his most recent battle against Jermell Charlo, the fight collected 700K PPV sales. These were just to name a few; over the years, Canelo has fought in increasingly profitable bouts.",
    "span": [
      3657,
      4184
    ]
  },
  {
    "doc_id": "mh_doc_dc17cfa263f250c17823",
    "node_id": "mh_n_chunk_0370236f0a9af43c7bf3",
    "page": 1,
    "snippet": "Charlo delivered a listless performance as Canelo bulled his way forward and tormented his opponent's body for much of the fight, scoring a knockdown in round seven to provide the only real drama of the evening.",
    "span": [
      614,
      825
    ]
  }
]
```
