# MultiHop RAG - Q39

**Question ID:** `Q-MH-039`

**Question:** Which company — featured in a TechCrunch article for cutting its workforce by 870 employees, and depicted by The Verge as the underdog in a legal battle against the company that has shaped the internet's appearance and local search rankings and is accused of harming news publishers' bottom lines through its practices — is involved in both scenarios?

- category: `multi_hop_traversal`
- answer type: `entity`
- confidence: `0.7`
- confidence basis: `model_synthesis_bounded_to_oracle_retrieved_public_passages`
- latency: `42121 ms`
- truncated: `None`
- reasoning trace: `T-MH-039`

## Answer

Epic

## Answer support

- `mh_e_9adff60f5ab0b57fada6`
- `mh_e_9f74e9b9588f27e8e350`
- `mh_n_chunk_8c11bca4473808961686`
- `mh_n_chunk_f2879f3bedbf94a32d94`

## Reasoning and evidence path

### 1. `firewall_check`

Status: **allowed**; executed before planner: `None`.

### 2. `bounded_search_expansion`

```json
{
  "error": null,
  "operation": "bounded_search_expansion",
  "search_terms": [
    "Yelp",
    "DuckDuckGo",
    "Tripadvisor",
    "Foursquare",
    "Nextdoor",
    "Angi",
    "870 employees TechCrunch",
    "Google lawsuit underdog",
    "Google local search rankings news publishers"
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
        "c0_0": "featured",
        "c0_1": "techcrunch",
        "c0_10": "shaped",
        "c0_11": "internet's",
        "c0_12": "appearance",
        "c0_13": "local",
        "c0_14": "search",
        "c0_15": "rankings",
        "c0_2": "article",
        "c0_3": "cutting",
        "c0_4": "workforce",
        "c0_5": "870",
        "c0_6": "employees",
        "c0_7": "depicted",
        "c0_8": "battle",
        "c0_9": "against",
        "c1_0": "accused",
        "c1_1": "harming",
        "c1_2": "news",
        "c1_3": "publishers",
        "c1_4": "bottom",
        "c1_5": "lines",
        "c1_6": "practices",
        "c1_7": "involved",
        "c1_8": "scenarios",
        "limit": 300,
        "s0": "s appearance and local search rankings and is accused of harming news publishers",
        "s1": "techcrunch",
        "s2": "the verge",
        "seed_limit": 30,
        "t0": "featured",
        "t1": "techcrunch",
        "t10": "legal",
        "t11": "battle",
        "t12": "local",
        "t13": "search",
        "t14": "rankings",
        "t15": "accused",
        "t16": "harming",
        "t17": "news",
        "t18": "publishers",
        "t19": "bottom",
        "t2": "article",
        "t20": "lines",
        "t21": "practices",
        "t22": "involved",
        "t23": "scenarios",
        "t3": "cutting",
        "t4": "workforce",
        "t5": "870",
        "t6": "employees",
        "t7": "depicted",
        "t8": "verge",
        "t9": "underdog"
      },
      "chunk_count": 20,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t12) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t13) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t14) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t15) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t16) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t17) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t18) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t19) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t20) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t21) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t22) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t23) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23) > 0 THEN 7 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_2) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_2) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_3) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_3) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_4) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_4) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_5) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_5) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_6) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_6) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_7) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_7) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_8) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_8) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_9) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_9) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_10) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_10) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_11) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_11) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_12) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_12) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_13) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_13) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_14) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_14) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_15) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_15) > 0 THEN 12 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c1_0) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_0) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_1) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_1) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_2) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_2) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_3) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_3) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_4) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_4) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_5) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_5) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_6) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_6) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_7) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_7) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_8) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_8) > 0 THEN 14 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t12),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t13),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t14),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t15),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t16),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t17),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t18),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t19),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t20),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t21),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t22),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t23),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
    },
    {
      "binds": {
        "c0_0": "featured",
        "c0_1": "techcrunch",
        "c0_10": "shaped",
        "c0_11": "internet's",
        "c0_12": "appearance",
        "c0_13": "local",
        "c0_14": "search",
        "c0_15": "rankings",
        "c0_2": "article",
        "c0_3": "cutting",
        "c0_4": "workforce",
        "c0_5": "870",
        "c0_6": "employees",
        "c0_7": "depicted",
        "c0_8": "battle",
        "c0_9": "against",
        "c1_0": "accused",
        "c1_1": "harming",
        "c1_2": "news",
        "c1_3": "publishers",
        "c1_4": "bottom",
        "c1_5": "lines",
        "c1_6": "practices",
        "c1_7": "involved",
        "c1_8": "scenarios",
        "limit": 300,
        "s0": "s appearance and local search rankings and is accused of harming news publishers",
        "s1": "techcrunch",
        "s2": "the verge",
        "seed_limit": 30,
        "t0": "yelp",
        "t1": "duckduckgo",
        "t10": "news",
        "t11": "publishers",
        "t12": "featured",
        "t13": "techcrunch",
        "t14": "article",
        "t15": "cutting",
        "t16": "workforce",
        "t17": "870",
        "t18": "employees",
        "t19": "depicted",
        "t2": "tripadvisor",
        "t20": "verge",
        "t21": "legal",
        "t22": "battle",
        "t23": "accused",
        "t24": "harming",
        "t25": "bottom",
        "t26": "lines",
        "t27": "practices",
        "t28": "involved",
        "t29": "scenarios",
        "t3": "foursquare",
        "t4": "nextdoor",
        "t5": "angi",
        "t6": "underdog",
        "t7": "local",
        "t8": "search",
        "t9": "rankings"
      },
      "chunk_count": 30,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 52 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 26 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 64 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 32 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 66 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 33 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 64 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 32 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 60 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 30 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 52 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 26 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 60 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 30 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 54 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 27 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 56 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 28 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 60 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 30 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 52 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 26 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 64 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 32 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t12) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t13) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t14) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t15) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t16) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t17) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t18) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t19) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t20) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t21) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t22) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t23) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t24) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t24) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t25) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t25) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t26) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t26) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t27) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t27) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t28) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t28) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t29) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t29) > 0 THEN 7 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_2) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_2) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_3) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_3) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_4) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_4) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_5) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_5) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_6) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_6) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_7) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_7) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_8) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_8) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_9) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_9) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_10) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_10) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_11) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_11) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_12) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_12) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_13) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_13) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_14) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_14) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_15) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_15) > 0 THEN 12 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c1_0) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_0) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_1) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_1) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_2) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_2) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_3) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_3) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_4) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_4) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_5) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_5) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_6) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_6) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_7) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_7) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c1_8) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c1_8) > 0 THEN 14 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t12),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t13),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t14),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t15),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t16),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t17),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t18),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t19),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t20),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t21),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t22),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t23),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t23)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t24),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t24)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t25),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t25)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t26),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t26)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t27),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t27)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t28),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t28)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t29),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t29)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1,:s2) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
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
  "edge_id": "mh_e_9adff60f5ab0b57fada6",
  "evidence": {
    "doc_id": "mh_doc_822705e0c8bc583bc4d9",
    "page": 1,
    "span": [
      266,
      567
    ]
  },
  "from": "mh_n_doc_822705e0c8bc583bc4d9",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_8c11bca4473808961686"
}
```

### 5. `edge_traversal`

```json
{
  "edge_id": "mh_e_9f74e9b9588f27e8e350",
  "evidence": {
    "doc_id": "mh_doc_77a817dff918b45a5c0c",
    "page": 1,
    "span": [
      0,
      572
    ]
  },
  "from": "mh_n_doc_77a817dff918b45a5c0c",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_f2879f3bedbf94a32d94"
}
```

### 6. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_8c11bca4473808961686"
  ],
  "claim": "Epic depicted as underdog vs Google in legal battle",
  "operation": "evidence_synthesis"
}
```

### 7. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_f2879f3bedbf94a32d94"
  ],
  "claim": "Google accused of harming news publishers via search/AI practices",
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

- `mh_n_doc_822705e0c8bc583bc4d9`
- `mh_n_chunk_8c11bca4473808961686`
- `mh_n_doc_77a817dff918b45a5c0c`
- `mh_n_chunk_f2879f3bedbf94a32d94`

### Edges

- `mh_e_9adff60f5ab0b57fada6`
- `mh_e_9f74e9b9588f27e8e350`

## Citations

```json
[
  {
    "doc_id": "mh_doc_822705e0c8bc583bc4d9",
    "node_id": "mh_n_chunk_8c11bca4473808961686",
    "page": 1,
    "span": [
      266,
      567
    ]
  },
  {
    "doc_id": "mh_doc_77a817dff918b45a5c0c",
    "node_id": "mh_n_chunk_f2879f3bedbf94a32d94",
    "page": 1,
    "span": [
      0,
      572
    ]
  }
]
```

## Retrieved context

```json
[
  {
    "doc_id": "mh_doc_822705e0c8bc583bc4d9",
    "node_id": "mh_n_chunk_8c11bca4473808961686",
    "page": 1,
    "snippet": "But now that both sides have made their opening arguments to a jury, I\u2019m not quite as sure. Because while Google spent most of its first day attempting to explain complicated ins and outs of business, Epic was able to paint a black-and-white picture of good and evil with itself as the clear underdog.",
    "span": [
      266,
      567
    ]
  },
  {
    "doc_id": "mh_doc_77a817dff918b45a5c0c",
    "node_id": "mh_n_chunk_f2879f3bedbf94a32d94",
    "page": 1,
    "snippet": "A new class action lawsuit filed this week in the U.S. District Court in D.C. accuses Google and parent company Alphabet of anticompetitive behavior in violation of U.S. antitrust law, the Sherman Act, and others, on behalf of news publishers. The case, filed by Arkansas-based publisher Helena World Chronicle, argues that Google \u201csiphons off\u201d news publishers\u2019 content, their readers and ad revenue through anticompetitive means. It also specifically cites new AI technologies like Google\u2019s Search Generative Experience (SGE) and Bard AI chatbot as worsening the problem.",
    "span": [
      0,
      572
    ]
  }
]
```
