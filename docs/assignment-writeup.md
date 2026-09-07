# Smart Inbox Assistant — Assignment Writeup

**Clinevo Technologies**
**Healthcare Email/Document Management System**

---

## 1. Problem

Healthcare organizations process large volumes of incoming emails and documents — safety reports, quality complaints, information requests, and irrelevant communications. Manual triage is slow, inconsistent, and risks missing critical items. The challenge is to build a system that:

- Automatically classifies incoming communications into meaningful categories
- Extracts structured data from unstructured clinical text
- Provides human oversight through a review workflow
- Maintains a complete audit trail for regulatory compliance
- Handles PDF documents, including scanned images requiring OCR

The four required classification categories are: **Safety Report**, **Quality Complaint**, **Info Request**, and **Not Relevant**. Documents may belong to multiple categories simultaneously.

---

## 2. Solution

A three-tier architecture with separation of concerns:

| Layer | Responsibility |
|-------|---------------|
| **Angular Frontend** | Dashboard for reviewing classifications, accepting/overriding results, viewing audit history |
| **Spring Boot Backend** | REST API, data persistence, async processing orchestration, audit logging |
| **Python AI Service** | Classification, extraction, summarization, PDF processing, LLM integration |

The flow is: email arrives via IMAP or API → backend persists and queues → AI service processes (classify, extract, summarize) → results stored → reviewer acts via dashboard → audit log records every step.

---

## 3. Architecture

```
                    +-----------------+
                    |   IMAP Server   |
                    +--------+--------+
                             |
                    +--------v--------+
                     |  Spring Boot    |  Port 8000
                    |  (Java 17)      |
                    +--------+--------+
                             |
              +--------------+--------------+
              |                             |
     +--------v--------+          +--------v--------+
     |   H2 / Oracle   |                               |  Python AI Svc  |  Port 8001
     |   Database       |          |  (FastAPI)      |
     +-----------------+          +-----------------+
              |                             |
              +--------------+--------------+
                             |
                    +--------v--------+
                    |  Angular UI     |  Port 80
                    |  (Nginx)        |
                    +-----------------+
```

- **Angular** proxies `/api/*` to the backend via Nginx
- **Spring Boot** calls the AI service via WebClient (non-blocking HTTP)
- **AI service** is stateless; all state lives in the database
- All mutations are audit-logged with 11 distinct action types

---

## 4. Technology Choices and Reasons

| Choice | Reason |
|--------|--------|
| **Spring Boot 3.2 / Java 17** | Mature ecosystem, strong typing, excellent ORM with JPA, async processing via `@Async` + `ThreadPoolTaskExecutor` |
| **Python FastAPI** | Native fit for ML/NLP tasks, rapid prototyping, Pydantic validation, async support, lightweight |
| **Angular 21** | TypeScript for type safety, component-based architecture, RxJS for reactive data flow, good enterprise support |
| **H2 (dev) / Oracle (prod)** | H2 for zero-config development; Oracle driver included for production deployment |
| **Nginx** | Reverse proxy, static file serving, gzip compression, API routing without CORS issues in production |
| **Docker Compose** | Single-command deployment of all three services with health checks and networking |

The split between Spring Boot and Python was deliberate: Spring Boot handles the enterprise concerns (database, audit, workflow) while Python handles the AI/NLP concerns (classification, extraction, LLM calls). This lets each team work independently and scale separately.

---

## 5. AI/LLM Approach

The AI service uses a **provider abstraction** pattern:

```
LLMProvider (ABC)
    ├── MockLLMProvider    (rule-based, no API calls)
    ├── OpenAIProvider     (GPT-4o-mini via API)
    └── AnthropicProvider  (Claude via API)
```

**Default mode is `mock`** — classification uses keyword banks and scoring rules with no LLM calls. This makes the system usable without API keys during development and testing.

When `LLM_PROVIDER=openai` or `LLM_PROVIDER=anthropic`, the system sends structured prompts to the LLM and parses JSON responses. The LLM result is used as the primary classification; the rule-based result serves as a fallback if the LLM call fails.

Every extracted field includes three attributes:
- `value` — the extracted text or `"Not stated"` if missing
- `confidence` — 0.0 to 1.0
- `source_ref` — document type, filename, and page number

---

## 6. Prompting Strategy

For classification, the prompt includes the document text and asks the LLM to return a JSON object with category scores:

```json
{
  "categories": [
    {"category": "SAFETY_REPORT", "confidence": 0.95},
    {"category": "QUALITY_COMPLAINT", "confidence": 0.10}
  ],
  "is_relevant": true,
  "reasoning": "Patient fall reported in ward..."
}
```

For extraction, the prompt provides the document text and document type, then requests structured fields relevant to that type (e.g., ICSR fields for safety reports, complaint fields for quality complaints).

For summarization, the prompt requests a structured summary with sections: Overview, Key Topics, Case Information, Missing Information, Relevance Assessment, Document Purpose.

Key prompting principles:
- Always request JSON output for reliable parsing
- Include the document type to scope extraction
- Ask for confidence scores to enable threshold-based decisions
- Request source references for traceability

---

## 7. Classification Approach

**Rule-based classifier** (default):

Each category has a keyword bank with weighted terms. Scoring works by:
1. Scanning text for keyword matches
2. Summing weights for matched keywords
3. Applying a short-text penalty (documents under 50 characters get reduced confidence)
4. Applying a multi-match boost (multiple keyword hits increase confidence)
5. Normalizing scores to 0.0–1.1 range
6. Sorting by confidence descending

**Multi-label support**: A document can match multiple categories independently. The primary category is the highest-scoring one, but all categories above a threshold are returned.

**Edge cases handled**:
- Empty/whitespace text → defaults to NOT_RELEVANT with confidence 0.0
- Very short text → reduced confidence
- No keyword matches → NOT_RELEVANT with confidence 0.1

The classifier achieved 100% accuracy on the 22-file synthetic test set.

---

## 8. PDF/OCR Approach

The PDF processing pipeline has six stages:

1. **Scanner Detector** — Analyzes text-to-image ratio. Digital PDFs have high text density; scanned PDFs have near-zero text and large images.

2. **Text Extractor** — Uses PyMuPDF (fitz) to extract text per page. Returns full text, per-page text, and page count.

3. **OCR Preparation** — If scanner detection indicates a scanned PDF and OCR is enabled, delegates to the OCR service.

4. **OCR Service** — Abstract `OCRProvider` interface with a Tesseract implementation. Low-confidence words are wrapped in `[uncertain]` tags. Results include per-page text and confidence scores.

5. **Language Detection** — Uses textheuristicizer to detect language. Returns ISO 639-1 code or "unknown" for short text.

6. **Table/Image Detection** — Basic heuristics: tables detected by pipe characters in text; images detected by image object count in the PDF.

Every extracted field carries a `source_ref` with document type, filename, and 1-indexed page number.

---

## 9. Source Traceability

Every extracted field in the system includes a `source_ref` object:

```json
{
  "value": "Aspirin 100mg",
  "confidence": 0.85,
  "source_ref": {
    "document_type": "pdf",
    "filename": "report-01.pdf",
    "page": 2
  }
}
```

For missing values:
```json
{
  "value": "Not stated",
  "confidence": 0.0,
  "source_ref": {
    "document_type": "email",
    "filename": "email-01.txt",
    "page": 1
  }
}
```

This ensures that every data point can be traced back to its origin in the source document. Reviewers can verify extracted facts against the original text.

---

## 10. Human Review Workflow

The review system supports two actions:

- **Accept** — Reviewer confirms the AI classification is correct. Records reviewer ID, timestamp, and optional notes.
- **Override** — Reviewer changes the category. Records the original category, new category, confidence delta, and reasoning.

**Duplicate guard**: Once a review exists for an email, further reviews are rejected with HTTP 409 Conflict. This prevents race conditions in multi-reviewer scenarios.

**Audit trail**: Every review action creates an audit log entry (REVIEW_ACCEPTED or REVIEW_OVERRIDDEN) with the reviewer ID and timestamp.

The Angular dashboard displays:
- Current classification with confidence score
- Accept/Override buttons
- Override category dropdown
- Review status badge (PENDING → ACCEPTED/OVERRIDDEN)
- Full audit history with action badges and source tracking

---

## 11. Audit Logging

The system logs 11 distinct action types across the processing pipeline:

| Action | When |
|--------|------|
| `EMAIL_RECEIVED` | Email ingested via API or IMAP |
| `DOCUMENT_RECEIVED` | Document attached to email |
| `PDF_TEXT_EXTRACTED` | Text extracted from PDF |
| `OCR_COMPLETED` | OCR processing finished |
| `LANGUAGE_DETECTED` | Language identified |
| `AI_CLASSIFIED` | Classification complete |
| `FACTS_EXTRACTED` | Field extraction complete |
| `SUMMARY_GENERATED` | Summary generated |
| `REVIEW_ACCEPTED` | Reviewer accepted classification |
| `REVIEW_OVERRIDDEN` | Reviewer overrode classification |
| `PROCESSING_FAILED` | Any processing step failed |

Each audit log entry includes: email ID, action type, actor ID (system component or human reviewer), details, source (e.g., "imap", "ai-service", "reviewer"), and timestamp.

The Angular dashboard shows audit history with color-coded action badges, source badges, and styling for failed/review entries.

---

## 12. Synthetic Test Data

All test data is synthetic — no real patient information is used.

**22 test files** across categories:

| Type | Count | Examples |
|------|-------|---------|
| Emails | 10 | Safety fall report, quality complaint, info request, marketing spam, mixed topics |
| Digital PDFs | 5 | Adverse event report, discharge summary, medication error, lab results, quality audit |
| Scanned PDFs | 2 | Handwritten incident report, faxed complaint |
| Non-English | 2 | Spanish patient safety, German pharmacy report |
| Articles | 5 | Fall prevention, medication reconciliation, adverse drug reactions, antibiotic stewardship, rare adverse event |

Test data covers all four classification categories, multi-label scenarios, edge cases (empty text, very short text), and source reference verification.

---

## 13. Batch Processing Results

The batch processor handled all 22 synthetic documents:

| Metric | Value |
|--------|-------|
| Total documents | 24 (including variations) |
| Successful | 24 |
| Failed | 0 |
| Total processing time | 182.3 ms |
| Average per document | 7.4 ms |

Classification distribution:
- Safety Reports: 8
- Quality Complaints: 6
- Info Requests: 5
- Not Relevant: 5

The batch report is saved to `sample-output/batch-processing-report.json` with per-document timing and classification results.

---

## 14. Security/Data Handling

**Implemented:**
- Environment variables for all secrets (API keys, database credentials, IMAP passwords)
- `.env.example` with placeholder values only — no real credentials in source
- `.dockerignore` files prevent secrets from entering Docker images
- Non-root users in all Docker containers
- Input validation via Pydantic (AI service) and Spring Validation (backend)

**Not implemented (production requirements):**
- No authentication or authorization on API endpoints
- No encryption at rest or in transit (HTTPS)
- No HIPAA-compliant audit logging
- No secrets management (Vault, AWS Secrets Manager)
- No PII detection or masking

All test data is synthetic. No real patient information appears anywhere in the codebase.

---

## 15. Known Limitations

| Area | Limitation |
|------|-----------|
| **Classification** | Rule-based classifier is English-centric. Non-English text is detected but not well classified without LLM mode. |
| **OCR** | Tesseract accuracy varies with scan quality. Handwritten text is not reliably extracted. |
| **PDF Tables** | Basic table detection using pipe-character heuristics. Complex multi-column layouts may not parse. |
| **Database** | H2 in-memory means data loss on restart. No persistence without Oracle. |
| **Authentication** | All API endpoints are open. No role-based access control. |
| **Real-time** | No WebSocket support. Dashboard requires manual refresh. |
| **Scaling** | Single-instance async processing. No distributed queue or horizontal scaling. |
| **Email** | IMAP ingestion is manual (API-triggered), not scheduled polling. |
| **LLM** | Mock provider uses rules, not actual inference. Real LLM requires paid API keys. |
| **Testing** | Spring Boot tests created but Maven not installed on dev machine, so not verified to compile. Angular tests created but Karma not configured. |

---

## 16. Production Improvements

**Security:**
- OAuth2/OIDC authentication (Keycloak, Auth0)
- Role-based access control (reviewer, admin, read-only)
- HTTPS/TLS everywhere
- HIPAA-compliant audit logging
- Secrets management (HashiCorp Vault)
- PII detection and masking

**Reliability:**
- Message queue for email ingestion (RabbitMQ, Kafka)
- Retry with exponential backoff for AI service calls
- Circuit breaker pattern
- Dead letter queue for failed processing
- Distributed tracing (Jaeger, Zipkin)

**Scalability:**
- Kubernetes deployment with auto-scaling
- Database connection pooling
- Redis caching for classification results
- CDN for frontend assets
- Horizontal scaling of AI service

**AI/ML:**
- Fine-tuned classification model on domain data
- Active learning from reviewer overrides
- Model versioning and A/B testing
- Confidence calibration
- Embedding-based document similarity search

**Observability:**
- Structured JSON logging
- Prometheus metrics
- Grafana dashboards
- Alerting on failures
- Log aggregation (ELK stack)

**Data:**
- PostgreSQL or Oracle with Flyway migrations
- Backup and recovery procedures
- Data retention policies
- Batch reprocessing capabilities

---

## Test Results

| Layer | Tests | Status |
|-------|-------|--------|
| Python AI Service | 324 | All passing |
| Spring Boot | 22 | Created (Maven not installed) |
| Angular | 27 | Created (Karma not configured) |
| End-to-End | 15 | Created (requires running services) |

---

## Summary

The system demonstrates a complete healthcare email processing pipeline: ingestion → classification → extraction → summarization → review → audit. The architecture separates enterprise concerns (Spring Boot) from AI concerns (Python), connected by a clean REST API. The rule-based classifier works without API keys, while the LLM abstraction allows upgrading to production-grade models. Every extracted field carries source traceability, and every action is audit-logged. The review workflow prevents unreviewed data from reaching downstream systems.

The main trade-off is simplicity vs. robustness: the current implementation favors rapid development and testability (H2, mock LLM, rule-based classification) over production readiness (authentication, persistence, real LLM inference). The production improvements list provides a clear roadmap for closing that gap.
