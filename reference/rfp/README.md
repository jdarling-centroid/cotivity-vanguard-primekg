# Vanguard Knowledge Management RFP Response Team Workspace

This folder has been prepared to store all resources, analyses, and logs for the **Vanguard Knowledge Management Vendor Evaluation Criteria POC**. 

When picking this task back up, use this document as a quick-start guide to understand the current state, what has been analyzed, and what the next development steps are.

---

## 1. Folder Contents

* **[vanguard_evaluation_criteria.pdf](file:///Users/jeremydarling/medical-classifier/cotiviti/ai-proposalresponse/vanguard_evaluation_criteria.pdf)**: The official vendor criteria PDF provided by Cotiviti.
* **[o26ai-migration-plan.md](file:///Users/jeremydarling/medical-classifier/cotiviti/ai-proposalresponse/o26ai-migration-plan.md)**: A technical consolidation plan using Oracle 26ai native queues (TxEQ), SecureFiles storage, vector search, and SQL/PGQ.
* **[cotiviti-clarification-questions.md](file:///Users/jeremydarling/medical-classifier/cotiviti/ai-proposalresponse/cotiviti-clarification-questions.md)**: Prepared technical Q&A questions for the client's clarification window.
* **[document-isolation-methodology.md](file:///Users/jeremydarling/medical-classifier/cotiviti/ai-proposalresponse/document-isolation-methodology.md)**: Ingestion sandboxing and LLM context isolation design to counter prompt injection threats.
* **[docs/competitive-advantage.md](file:///Users/jeremydarling/medical-classifier/cotiviti/ai-proposalresponse/docs/competitive-advantage.md)**: Details on why our document-boundary detection and page-assembly ingestion pipeline is a major competitive advantage.
* **[docs/model-routing-strategy.md](file:///Users/jeremydarling/medical-classifier/cotiviti/ai-proposalresponse/docs/model-routing-strategy.md)**: System design for routing queries through SkillOpt (Orinth/large LLMs) and routing document extraction to small, local on-device SLMs (MiniCPM5).
* **[mock_templates/](file:///Users/jeremydarling/medical-classifier/cotiviti/ai-proposalresponse/mock_templates/)**: Reference JSON/JSONL output templates matching the RFP Section 8 schemas.
* **[conversation_transcript.jsonl](file:///Users/jeremydarling/medical-classifier/cotiviti/ai-proposalresponse/conversation_transcript.jsonl)**: A compact JSONL transcript of the strategic conversation assessing the POC.
* **[conversation_transcript_full.jsonl](file:///Users/jeremydarling/medical-classifier/cotiviti/ai-proposalresponse/conversation_transcript_full.jsonl)**: The full untruncated JSONL conversation log.

---

## 2. Summary of Strategic Decisions & Status

### A. Architectural Stance
* **The Core Gap:** The RFP requires a **GraphRAG system with an active conversational reasoning agent** capable of answering multi-hop queries and producing step-by-step reasoning traces (`qa-results.jsonl`, `reasoning-traces.json`). The current POC is only an **ingestion/retrieval engine** and explicitly defers the agent layer.
* **The Remediation:** We will build a lightweight python agent layer (e.g., using LangGraph or a custom runner) that interacts with our existing MCP server tools.

### B. Infrastructure Decisions
* **OCI Bypass:** We do not need OCI's proprietary AI services (Vision, Doc Understanding, Generative AI). We will rewrite the adapters in [oci_impl.py](file:///Users/jeremydarling/medical-classifier/apps/medical_classifier/shared/adapters/oci_impl.py) to use local python libraries (like `pdfplumber` / `pytesseract`) and public/local API endpoints (like OpenAI or Ollama/Llama-3).
* **No Redis Needed:** For simplicity and rapid verification, we can run **Oracle Database in a container** (using the official `container-registry.oracle.com/database/free:latest` image) and use the native file-based queues (`LocalQueue`) and local directory storage (`LocalStorage`) already built into the POC.

---

## 3. Immediate Next Steps for the Developer

1. **Deploy Local Database:** Pull and start the Oracle Database Free container image:
   ```bash
   docker run --name oracle-free -d -p 1521:1521 -e ORACLE_PWD=YourStrongPassword container-registry.oracle.com/database/free:latest
   ```
2. **Build the GraphRAG Agent Layer:** Implement the Q&A execution loop and reasoning trace exporter to meet the schema specs in Section 8.2 and 8.3 of the RFP.
3. **Implement LLM Adapters:** Swap the OCI stubs in `oci_impl.py` for actual OpenAI/Anthropic/Ollama APIs. Include prompts to extract clinical attributes (negation, temporality, experiencer) to clear the Stage 2 safety gating.
4. **Complete Search Vector TODOs:** Complete the vector similarity and graph reranking placeholders in [repository.py](file:///Users/jeremydarling/medical-classifier/apps/medical_classifier/shared/repository.py#L1131-L1132).
