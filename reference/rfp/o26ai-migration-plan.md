# Oracle 26ai Consolidation & Migration Plan

This document outlines the migration plan to consolidate all backend services of the **Vanguard Knowledge Management POC** into a single **Oracle 26ai (or 23ai) Database container**. 

By leveraging native database capabilities, we can eliminate external OCI service requirements, local file-system dependencies, and Redis instances. Oracle 26ai will serve as the single source of truth for **relational data, vector search, property graph queries, object storage, and message queuing**.

---

## 1. Core Consolidation Architecture

Instead of a multi-resource local or cloud deployment, we will utilize the full convergence capabilities of the Oracle database:

```text
+-----------------------------------------------------------------------------------+
|                            Oracle 26ai Database Container                         |
|                                                                                   |
|  +--------------------------+  +--------------------------+  +-----------------+  |
|  |     Relational Schema    |  |     AI Vector Search     |  | Property Graph  |  |
|  | (uploads, nodes, edges)  |  |  (embeddings table &    |  |  (SQL/PGQ index |  |
|  |                          |  |   vector COSINE index)   |  |   traversals)   |  |
|  +--------------------------+  +--------------------------+  +-----------------+  |
|                                                                                   |
|  +--------------------------+  +--------------------------+                       |
|  |     Message Queuing      |  |      Object Storage      |                       |
|  |   (Transactional Event   |  |   (SecureFiles BLOBs /   |                       |
|  |      Queue - TxEQ)       |  |     artifacts table)     |                       |
|  +--------------------------+  +--------------------------+                       |
+-----------------------------------------------------------------------------------+
```

---

## 2. Component Migration Details

### A. Message Queuing: Migrate from LocalQueue to Oracle Advanced Queuing (AQ/TxEQ)
* **Goal:** Replace the file-locked [LocalQueue](file:///Users/jeremydarling/medical-classifier/apps/medical_classifier/shared/queue.py#L40) and avoid spinning up Redis.
* **Mechanism:** Use **Oracle Transactional Event Queuing (TxEQ)**. TxEQ allows queues to be managed directly inside database tables.
* **Benefits:** 
  * **Transactional Guarantees:** Message consumption (`ACK`/`NACK`) occurs in the same database transaction as the graph/node updates. If a worker fails mid-job, the transaction rolls back, and the message automatically returns to the queue (exactly-once processing).
  * **Python Integration:** The `oracledb` python driver has native support for Advanced Queuing via the `connection.queue()` API.
* **Migration Actions:**
  1. Define queue tables and create queues (`page_split`, `page_process`, `document_assemble`, `index`) in the migration script.
  2. Implement an `OracleQueue` class in [queue.py](file:///Users/jeremydarling/medical-classifier/apps/medical_classifier/shared/queue.py) implementing the `Queue` protocol.

### B. Document & Image Storage: Migrate from Local Filesystem to SecureFiles LOBs
* **Goal:** Replace `./.local-storage` (and OCI Object Storage) so binary PDFs and rendered images live inside the database.
* **Mechanism:** Use Oracle **SecureFiles BLOBs** (Binary Large Objects) with compression enabled.
* **Benefits:**
  * Single backup footprint.
  * No file-system permission issues in containerized environments.
  * Easy retrieval of artifacts directly through FastAPI binary streaming.
* **Migration Actions:**
  1. Update the `artifacts` table schema in [oracle.sql](file:///Users/jeremydarling/medical-classifier/schemas/oracle.sql#L196) to include a `file_data BLOB` column.
  2. Implement a `DatabaseStorage` class in [storage.py](file:///Users/jeremydarling/medical-classifier/apps/medical_classifier/shared/storage.py) implementing the `ObjectStore` protocol.

### C. Semantic Search: Implement Native AI Vector Search
* **Goal:** Complete the semantic vector search `TODO` in [repository.py](file:///Users/jeremydarling/medical-classifier/apps/medical_classifier/shared/repository.py#L1131).
* **Mechanism:** Use Oracle 23ai/26ai native `VECTOR` data types and vector distance operators.
* **Migration Actions:**
  1. Use a local Python-based embedder (like `sentence-transformers` or `onnxruntime` loaded inside our worker container) to generate 384-dimensional or 1536-dimensional float32 arrays.
  2. Write the SQL query in `Repository.search` using the native vector operator:
     ```sql
     SELECT node_id, COSINE_DISTANCE(embedding, :query_vector) AS dist
     FROM embeddings
     ORDER BY dist
     FETCH FIRST :limit ROWS ONLY;
     ```

---

## 3. Migration Roadmap & Technical Steps

### Phase 1: Database DDL Updates (1-2 Days)
Execute the following updates to [oracle.sql](file:///Users/jeremydarling/medical-classifier/schemas/oracle.sql):
1. **SecureFiles Storage:** Add the `file_data` binary column:
   ```sql
   ALTER TABLE artifacts ADD (file_data BLOB) 
   LOB (file_data) STORE AS SECUREFILES (COMPRESS HIGH);
   ```
2. **Oracle AQ Setup:** Create the PL/SQL blocks to initialize Oracle Advanced Queuing:
   ```sql
   BEGIN
     DBMS_AQADM.CREATE_QUEUE_TABLE(
       queue_table        => 'mc_queue_table',
       queue_payload_type => 'RAW'
     );
     DBMS_AQADM.CREATE_QUEUE(
       queue_name  => 'page_process_queue',
       queue_table => 'mc_queue_table'
     );
     DBMS_AQADM.START_QUEUE(queue_name => 'page_process_queue');
   END;
   /
   ```

### Phase 2: Python Adapter Extensions (3-4 Days)
1. **Oracle Queue Provider:**
   Create the adapter in `queue.py`:
   ```python
   class OracleQueue:
       def __init__(self, conn) -> None:
           self.conn = conn
       
       def publish(self, channel: str, payload: dict) -> str:
           queue = self.conn.queue(f"{channel}_queue")
           msg = self.conn.msgproperties(payload=json.dumps(payload).encode('utf-8'))
           queue.enqOne(msg)
           return msg.msgid.hex()
   ```
2. **Oracle Storage Provider:**
   Create the storage adapter in `storage.py` that executes:
   ```sql
   INSERT INTO artifacts (artifact_id, node_id, artifact_role, object_path, media_type, byte_size, checksum_sha256, file_data)
   VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
   ```

### Phase 3: Integration & Testing (2 Days)
1. Configure `config.yaml` to set storage and queue backends to `"oracle"`:
   ```yaml
   storage:
     backend: oracle
   queue:
     backend: oracle
   ```
2. Run local docker-compose testing with the containerized database.

---

## 4. Architectural Tradeoffs

| Factor | Consolidated Oracle 26ai Approach | Distributed Approach (Redis + S3/OCI Storage) |
| :--- | :--- | :--- |
| **Operational Complexity**| **Very Low** (Single container dependency, easy to deploy locally or to OCI Autonomous DB) | **Moderate** (Must provision, secure, and monitor Redis, Object Storage, and SQL DB) |
| **Transactional Safety** | **Maximum** (All data, queues, and files are updated in single transactions; zero orphan files or lost queue entries) | **Lower** (No distributed transactions; queue can pull message but database write fails, leading to inconsistency) |
| **Database Load** | **Higher** (Database processes message queuing and LOB file streams alongside relational/vector queries) | **Lower** (Database only handles relational metadata; queuing and file streaming are offloaded) |
| **Storage Cost** | **Higher** (Database storage block prices are typically higher than object storage prices) | **Lower** (Raw PDFs are stored on cheap Object Storage) |

**Conclusion:** For a POC or evaluation run (like the Cotiviti benchmark), the **Consolidated Oracle 26ai** approach is vastly superior. It eliminates deployment overhead, simplifies local setup on developers' machines, and guarantees data integrity during multi-stage worker failures.
