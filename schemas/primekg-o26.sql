-- PrimeKG on Oracle 26ai. Statements are separated by a lone `/` on its own
-- line; the loader executes each and tolerates "already exists" errors so the
-- schema is idempotent. Native predicate + display_relation are preserved on
-- every edge (never collapsed).

-- Section: TABLES ------------------------------------------------------------

CREATE TABLE pk_nodes (
  node_id    VARCHAR2(64)         NOT NULL,
  node_index NUMBER               NOT NULL,
  node_type  VARCHAR2(40),
  name       VARCHAR2(2000),
  source     VARCHAR2(64),
  code       VARCHAR2(512),
  name_norm  VARCHAR2(1000),
  name_vec   VECTOR(384, FLOAT32),
  CONSTRAINT pk_nodes_pk PRIMARY KEY (node_id)
)
/

CREATE TABLE pk_edges (
  edge_id          VARCHAR2(96)  NOT NULL,
  source_node_id   VARCHAR2(64)  NOT NULL,
  target_node_id   VARCHAR2(64)  NOT NULL,
  predicate        VARCHAR2(64)  NOT NULL,
  display_relation VARCHAR2(64),
  CONSTRAINT pk_edges_pk PRIMARY KEY (edge_id)
)
/

-- One row per completed load, keyed by the source checksum + relation subset so
-- re-running is a no-op and never double-inserts.
CREATE TABLE pk_load_journal (
  id           NUMBER GENERATED ALWAYS AS IDENTITY,
  kg_checksum  VARCHAR2(64),
  relations    VARCHAR2(1000),
  nodes_loaded NUMBER,
  edges_loaded NUMBER,
  status       VARCHAR2(20),
  updated_at   TIMESTAMP DEFAULT SYSTIMESTAMP,
  CONSTRAINT pk_load_journal_pk PRIMARY KEY (id)
)
/

-- Section: INDEXES (created post-load by the loader) -------------------------

CREATE INDEX pk_edges_src ON pk_edges (predicate, display_relation, source_node_id)
/

CREATE INDEX pk_edges_tgt ON pk_edges (predicate, display_relation, target_node_id)
/

CREATE INDEX pk_nodes_type_norm ON pk_nodes (node_type, name_norm)
/

CREATE INDEX pk_nodes_norm ON pk_nodes (name_norm)
/

-- Section: PROPERTY GRAPH ----------------------------------------------------

CREATE PROPERTY GRAPH primekg
  VERTEX TABLES (
    pk_nodes KEY (node_id)
      LABEL node PROPERTIES (node_id, node_type, name, name_norm)
  )
  EDGE TABLES (
    pk_edges KEY (edge_id)
      SOURCE      KEY (source_node_id) REFERENCES pk_nodes (node_id)
      DESTINATION KEY (target_node_id) REFERENCES pk_nodes (node_id)
      LABEL rel PROPERTIES (edge_id, predicate, display_relation)
  )
/
