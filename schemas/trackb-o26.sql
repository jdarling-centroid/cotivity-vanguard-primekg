CREATE TABLE mh_nodes (
  node_id          VARCHAR2(96) PRIMARY KEY,
  node_type        VARCHAR2(64) NOT NULL,
  label            VARCHAR2(2000) NOT NULL,
  text_content     CLOB,
  provenance_json CLOB NOT NULL CHECK (provenance_json IS JSON),
  attributes_json CLOB CHECK (attributes_json IS JSON)
)
/
CREATE TABLE mh_edges (
  edge_id          VARCHAR2(96) PRIMARY KEY,
  subject_id       VARCHAR2(96) NOT NULL REFERENCES mh_nodes(node_id),
  predicate        VARCHAR2(96) NOT NULL,
  object_id        VARCHAR2(96) NOT NULL REFERENCES mh_nodes(node_id),
  provenance_json CLOB NOT NULL CHECK (provenance_json IS JSON)
)
/
CREATE INDEX mh_nodes_type_ix ON mh_nodes(node_type)
/
CREATE INDEX mh_edges_subject_ix ON mh_edges(subject_id, predicate)
/
CREATE INDEX mh_edges_object_ix ON mh_edges(object_id, predicate)
/
CREATE TABLE mh_load_journal (
  artifact_sha256 VARCHAR2(64) PRIMARY KEY,
  nodes_loaded    NUMBER NOT NULL,
  edges_loaded    NUMBER NOT NULL,
  status          VARCHAR2(32) NOT NULL,
  updated_at      TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
)
/
