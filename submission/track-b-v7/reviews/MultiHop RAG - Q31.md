# MultiHop RAG - Q31

**Question ID:** `Q-MH-031`

**Question:** Which sportsbook, highlighted by both 'Sporting News' and 'CBSSports.com', provides a cash-out option for MLB bets, a welcome bonus plus NBA promotions, and up to $1,000 in bonus bets for new customers in Kentucky and Vermont if their first bet does not win?

- category: `multi_hop_traversal`
- answer type: `entity`
- confidence: `0.7`
- confidence basis: `model_synthesis_bounded_to_oracle_retrieved_public_passages`
- latency: `13865 ms`
- truncated: `None`
- reasoning trace: `T-MH-031`

## Answer

Caesars Sportsbook

## Answer support

- `mh_e_77acff3935187d0b3d2c`
- `mh_e_0bea4c6da3a09ce3d20e`
- `mh_e_b062373d3830b4a3da73`
- `mh_e_4176c01429f20d4a5d5a`
- `mh_n_chunk_0a60e55d24dbcb2d9f1d`
- `mh_n_chunk_007e6b762684de8fca9f`
- `mh_n_chunk_10de928e08a285431897`
- `mh_n_chunk_216e4b8d659f5a76a352`

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
        "c0_0": "sportsbook",
        "c0_1": "highlighted",
        "c0_10": "customers",
        "c0_11": "kentucky",
        "c0_12": "vermont",
        "c0_13": "first",
        "c0_14": "bet",
        "c0_15": "win",
        "c0_2": "sporting",
        "c0_3": "news",
        "c0_4": "cbssports.com",
        "c0_5": "provides",
        "c0_6": "cash-out",
        "c0_7": "option",
        "c0_8": "000",
        "c0_9": "new",
        "limit": 300,
        "s0": "sporting news",
        "s1": "cbssports.com",
        "seed_limit": 30,
        "t0": "sportsbook",
        "t1": "highlighted",
        "t10": "welcome",
        "t11": "bonus",
        "t12": "plus",
        "t13": "nba",
        "t14": "promotions",
        "t15": "000",
        "t16": "new",
        "t17": "customers",
        "t18": "kentucky",
        "t19": "vermont",
        "t2": "sporting",
        "t20": "first",
        "t21": "bet",
        "t22": "win",
        "t3": "news",
        "t4": "cbssports.com",
        "t5": "provides",
        "t6": "cash-out",
        "t7": "option",
        "t8": "mlb",
        "t9": "bets"
      },
      "chunk_count": 20,
      "query": "WITH ranked AS ( SELECT n.node_id chunk_id,n.text_content,n.provenance_json, (GREATEST((CASE WHEN INSTR(LOWER(n.text_content), :t0) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t1) > 0 THEN 18 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1) > 0 THEN 9 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t2) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t3) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t4) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t5) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t6) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t7) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t8) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t9) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t10) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t11) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t12) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t13) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t14) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t15) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t16) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t17) > 0 THEN 14 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17) > 0 THEN 7 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t18) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t19) > 0 THEN 10 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19) > 0 THEN 5 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t20) > 0 THEN 6 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20) > 0 THEN 3 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t21) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21) > 0 THEN 1 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :t22) > 0 THEN 2 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22) > 0 THEN 1 ELSE 0 END),(CASE WHEN INSTR(LOWER(n.text_content), :c0_0) > 0 THEN 32 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_0) > 0 THEN 16 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_1) > 0 THEN 36 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_1) > 0 THEN 18 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_2) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_2) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_3) > 0 THEN 8 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_3) > 0 THEN 4 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_4) > 0 THEN 40 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_4) > 0 THEN 20 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_5) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_5) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_6) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_6) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_7) > 0 THEN 16 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_7) > 0 THEN 8 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_8) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_8) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_9) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_9) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_10) > 0 THEN 28 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_10) > 0 THEN 14 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_11) > 0 THEN 24 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_11) > 0 THEN 12 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_12) > 0 THEN 20 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_12) > 0 THEN 10 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_13) > 0 THEN 12 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_13) > 0 THEN 6 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_14) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_14) > 0 THEN 2 ELSE 0 END + CASE WHEN INSTR(LOWER(n.text_content), :c0_15) > 0 THEN 4 WHEN INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :c0_15) > 0 THEN 2 ELSE 0 END))) score,CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1) THEN 1 ELSE 0 END source_match, JSON_VALUE(n.provenance_json,'$.doc_id') doc_id, JSON_VALUE(n.attributes_json,'$.source') source_name FROM mh_nodes n WHERE n.node_type='TextBlock' AND (GREATEST(INSTR(LOWER(n.text_content), :t0),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t0)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t1),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t1)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t2),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t2)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t3),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t3)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t4),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t4)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t5),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t5)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t6),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t6)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t7),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t7)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t8),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t8)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t9),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t9)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t10),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t10)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t11),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t11)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t12),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t12)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t13),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t13)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t14),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t14)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t15),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t15)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t16),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t16)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t17),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t17)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t18),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t18)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t19),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t19)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t20),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t20)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t21),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t21)) > 0 OR GREATEST(INSTR(LOWER(n.text_content), :t22),INSTR(LOWER(JSON_VALUE(n.attributes_json,'$.document_title')), :t22)) > 0)), document_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC,chunk_id) document_rank FROM ranked r), source_ranked AS ( SELECT r.*,ROW_NUMBER() OVER (PARTITION BY source_name ORDER BY score DESC,chunk_id) source_rank FROM document_ranked r WHERE document_rank=1), seeds AS ( SELECT * FROM source_ranked ORDER BY CASE WHEN source_match=1 AND source_rank<=15 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :seed_limit ROWS ONLY), top_document_seeds AS ( SELECT * FROM seeds ORDER BY source_match DESC,source_rank ASC,score DESC,chunk_id FETCH FIRST 20 ROWS ONLY), expanded_ids AS ( SELECT related.subject_id chunk_id,MAX(s.score)-1 score FROM seeds s JOIN mh_edges mention ON mention.subject_id=s.chunk_id AND mention.predicate='mentions' JOIN mh_edges related ON related.object_id=mention.object_id AND related.predicate='mentions' GROUP BY related.subject_id), document_expanded_ids AS ( SELECT sibling.object_id chunk_id,r.score FROM top_document_seeds s JOIN mh_edges parent ON parent.object_id=s.chunk_id AND parent.predicate='contains_chunk' JOIN mh_edges sibling ON sibling.subject_id=parent.subject_id AND sibling.predicate='contains_chunk' JOIN ranked r ON r.chunk_id=sibling.object_id), candidate_ids AS ( SELECT chunk_id,MAX(score) score,MIN(priority) priority FROM ( SELECT chunk_id,score,0 priority FROM seeds UNION ALL SELECT chunk_id,score,1 priority FROM expanded_ids UNION ALL SELECT chunk_id,score,0 priority FROM document_expanded_ids) GROUP BY chunk_id), candidate_ranked AS ( SELECT c.chunk_id,n.text_content,n.provenance_json,c.score,c.priority, CASE WHEN LOWER(JSON_VALUE(n.attributes_json,'$.source')) IN (:s0,:s1) THEN 1 ELSE 0 END source_match, ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(n.attributes_json,'$.source') ORDER BY c.score DESC,c.chunk_id) source_rank FROM candidate_ids c JOIN mh_nodes n ON n.node_id=c.chunk_id), top_chunks AS ( SELECT * FROM candidate_ranked ORDER BY priority, CASE WHEN source_match=1 AND source_rank<=20 THEN 0 ELSE 1 END, score DESC,source_rank,chunk_id FETCH FIRST :limit ROWS ONLY) SELECT t.chunk_id,e.subject_id document_id,e.edge_id,t.text_content, t.provenance_json,d.attributes_json,d.label,t.score FROM top_chunks t JOIN mh_edges e ON e.object_id=t.chunk_id AND e.predicate='contains_chunk' JOIN mh_nodes d ON d.node_id=e.subject_id ORDER BY t.score DESC,t.chunk_id"
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
  "edge_id": "mh_e_77acff3935187d0b3d2c",
  "evidence": {
    "doc_id": "mh_doc_f2afc4281f6567c71fb2",
    "page": 1,
    "span": [
      2675,
      2693
    ]
  },
  "from": "mh_n_doc_f2afc4281f6567c71fb2",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_0a60e55d24dbcb2d9f1d"
}
```

### 5. `edge_traversal`

```json
{
  "edge_id": "mh_e_0bea4c6da3a09ce3d20e",
  "evidence": {
    "doc_id": "mh_doc_c117b3b60be6bf903dc0",
    "page": 1,
    "span": [
      8895,
      9020
    ]
  },
  "from": "mh_n_doc_c117b3b60be6bf903dc0",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_007e6b762684de8fca9f"
}
```

### 6. `edge_traversal`

```json
{
  "edge_id": "mh_e_b062373d3830b4a3da73",
  "evidence": {
    "doc_id": "mh_doc_22cc5ea346f06b5a68d2",
    "page": 1,
    "span": [
      5439,
      6143
    ]
  },
  "from": "mh_n_doc_22cc5ea346f06b5a68d2",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_10de928e08a285431897"
}
```

### 7. `edge_traversal`

```json
{
  "edge_id": "mh_e_4176c01429f20d4a5d5a",
  "evidence": {
    "doc_id": "mh_doc_c117b3b60be6bf903dc0",
    "page": 1,
    "span": [
      2951,
      2958
    ]
  },
  "from": "mh_n_doc_c117b3b60be6bf903dc0",
  "operation": "edge_traversal",
  "predicate": "contains_chunk",
  "to": "mh_n_chunk_216e4b8d659f5a76a352"
}
```

### 8. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_0a60e55d24dbcb2d9f1d",
    "mh_n_chunk_10de928e08a285431897"
  ],
  "claim": "Caesars highlighted in Sporting News MLB and NBA betting coverage with welcome bonuses and promos",
  "operation": "evidence_synthesis"
}
```

### 9. `evidence_synthesis`

```json
{
  "chunk_node_ids": [
    "mh_n_chunk_007e6b762684de8fca9f",
    "mh_n_chunk_216e4b8d659f5a76a352"
  ],
  "claim": "Caesars highlighted in CBSSports.com Kentucky sportsbooks article with app and bonus details",
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

- `mh_n_doc_f2afc4281f6567c71fb2`
- `mh_n_chunk_0a60e55d24dbcb2d9f1d`
- `mh_n_doc_c117b3b60be6bf903dc0`
- `mh_n_chunk_007e6b762684de8fca9f`
- `mh_n_doc_22cc5ea346f06b5a68d2`
- `mh_n_chunk_10de928e08a285431897`
- `mh_n_chunk_216e4b8d659f5a76a352`

### Edges

- `mh_e_77acff3935187d0b3d2c`
- `mh_e_0bea4c6da3a09ce3d20e`
- `mh_e_b062373d3830b4a3da73`
- `mh_e_4176c01429f20d4a5d5a`

## Citations

```json
[
  {
    "doc_id": "mh_doc_f2afc4281f6567c71fb2",
    "node_id": "mh_n_chunk_0a60e55d24dbcb2d9f1d",
    "page": 1,
    "span": [
      2675,
      2693
    ]
  },
  {
    "doc_id": "mh_doc_c117b3b60be6bf903dc0",
    "node_id": "mh_n_chunk_007e6b762684de8fca9f",
    "page": 1,
    "span": [
      8895,
      9020
    ]
  },
  {
    "doc_id": "mh_doc_22cc5ea346f06b5a68d2",
    "node_id": "mh_n_chunk_10de928e08a285431897",
    "page": 1,
    "span": [
      5439,
      6143
    ]
  },
  {
    "doc_id": "mh_doc_c117b3b60be6bf903dc0",
    "node_id": "mh_n_chunk_216e4b8d659f5a76a352",
    "page": 1,
    "span": [
      2951,
      2958
    ]
  }
]
```

## Retrieved context

```json
[
  {
    "doc_id": "mh_doc_f2afc4281f6567c71fb2",
    "node_id": "mh_n_chunk_0a60e55d24dbcb2d9f1d",
    "page": 1,
    "snippet": "Caesars Sportsbook",
    "span": [
      2675,
      2693
    ]
  },
  {
    "doc_id": "mh_doc_c117b3b60be6bf903dc0",
    "node_id": "mh_n_chunk_007e6b762684de8fca9f",
    "page": 1,
    "snippet": "Easy deposits and withdrawals, 24/7 access, safe and secure transactions Caesars iOS and Android apps, desktop and mobile web",
    "span": [
      8895,
      9020
    ]
  },
  {
    "doc_id": "mh_doc_22cc5ea346f06b5a68d2",
    "node_id": "mh_n_chunk_10de928e08a285431897",
    "page": 1,
    "snippet": "As one of the most recognizable names in the gambling industry, BetMGM knows how to attract and keep customers with competitive odds for all bet types, including futures bets and the NBA Rookie of the Year. BetMGM offers many deposit and withdrawal options and 24/7 customer service, and generous sports betting bonuses and promotions. Caesars Sportsbook: Caesars knows its way around sports betting when you use its app and online sportsbook. It offers favorable odds for almost every bet type, including NBA ROTY betting, and offers a nice variety of deposit and withdrawal options. Additionally, Caesars has a competitive welcome bonus for new players and runs NBA betting promos for existing players.",
    "span": [
      5439,
      6143
    ]
  },
  {
    "doc_id": "mh_doc_c117b3b60be6bf903dc0",
    "node_id": "mh_n_chunk_216e4b8d659f5a76a352",
    "page": 1,
    "snippet": "CAESARS",
    "span": [
      2951,
      2958
    ]
  }
]
```
