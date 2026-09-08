# Smart Inbox Assistant for Healthcare

Healthcare email and document management system with AI-powered classification, extraction, and review workflow.


---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Architecture](#3-architecture)
4. [Architecture Diagram](#4-architecture-diagram)
5. [Tech Stack](#5-tech-stack)
6. [Project Structure](#6-project-structure)
7. [Prerequisites](#7-prerequisites)
8. [Environment Variables](#8-environment-variables)
9. [Oracle Setup](#9-oracle-setup)
10. [Python AI Service Setup](#10-python-ai-service-setup)
11. [Spring Boot Setup](#11-spring-boot-setup)
12. [Angular Setup](#12-angular-setup)
13. [Email/IMAP Configuration](#13-emailimap-configuration)
14. [How to Run Locally](#14-how-to-run-locally)
15. [Processing Test Emails](#15-processing-test-emails)
16. [Batch Processing](#16-batch-processing)
17. [Running Tests](#17-running-tests)
18. [Sample Outputs](#18-sample-outputs)
19. [Known Limitations](#19-known-limitations)
20. [AI/Data-Handling Trade-offs](#20-aidata-handling-trade-offs)
21. [Production Improvements](#21-production-improvements)

---

## 1. Project Overview

Smart Inbox Assistant is a healthcare email management system that automatically classifies, prioritizes, and processes incoming emails and documents. It uses AI to categorize communications into actionable categories, extract structured data from unstructured text, and present results through a web-based dashboard with human-in-the-loop review.

**Key capabilities:**

- Multi-category classification (Safety Reports, Quality Complaints, Info Requests, Not Relevant)
- Structured fact extraction from clinical text (ICSR forms, complaint details)
- Document summarization with 10-15 sentence structured summaries
- PDF processing with OCR support for scanned documents
- Human review workflow with accept/override functionality
- Complete audit trail with 11 action types
- Batch processing for bulk document ingestion

---

## 2. Problem Statement

Healthcare organizations receive hundreds of emails daily spanning safety reports, quality complaints, information requests, and irrelevant communications. Manual triage is slow, inconsistent, and error-prone. Critical safety reports can be delayed, complaints can be missed, and staff spend excessive time on low-value sorting.

**This system solves:**

- **Speed**: Automated classification reduces triage time from hours to seconds
- **Consistency**: Rule-based and AI classification eliminates human bias in initial sorting
- **Completeness**: Structured extraction ensures no critical data point is overlooked
- **Traceability**: Full audit trail from ingestion through final review
- **Scalability**: Batch processing handles volume spikes without additional staff

---

## 3. Architecture

| Layer | Component | Technology | Port |
|-------|-----------|------------|------|
| Presentation | Frontend | Angular 21 + Nginx | 80 |
| API Gateway | Backend | Spring Boot 3.2 (Java 17) | 8000 |
| AI Processing | AI Service | Python FastAPI | 8001 |
| Data Store | Database | H2 (dev) / Oracle (prod) | - |
| Email Ingestion | IMAP Client | Jakarta Mail | - |

**Data flow:**

```
Email (IMAP) --> Spring Boot --> AI Service --> Database --> Angular --> Reviewer --> Audit
```

**Service communication:**

- Angular proxies `/api/*` requests to Spring Boot via Nginx
- Spring Boot calls AI Service via WebClient (HTTP)
- AI Service is stateless; all state lives in the database
- All mutations are audit-logged with 11 distinct action types

---

## 4. Architecture Diagram

```
+------------------+       +-------------------+       +------------------+
|                  |       |                   |       |                  |
|    Angular UI    |<----->|  Spring Boot API  |<----->|  Python AI       |
|    (Nginx)       |       |  (Java 17)        |       |  Service         |
|    Port 80       |       |  Port 8000        |       |  Port 8001       |
|                  |       |                   |       |                  |
+------------------+       +-------------------+       +------------------+
        |                          |                          |
        |                     +----+----+                     |
        |                     |         |                     |
        |                     v         v                     |
        |              +----------+ +----------+              |
        |              | H2 /     | | WebClient|              |
        |              | Oracle   | | (calls)  |              |
        |              +----------+ +----------+              |
        |                     |                          |
        +---------------------+--------------------------+
                              |
                     +--------v--------+
                     |                 |
                     |  Audit Trail    |
                     |  (11 actions)   |
                     |                 |
                     +-----------------+

  IMAP Email Server -----> Spring Boot (ingestion)
  Reviewer (human)  -----> Angular UI (accept/override)
```

**Processing pipeline:**

```
Email Received
    |
    v
[1] EMAIL_RECEIVED (audit)
    |
    v
[2] PDF Text Extraction / OCR
    |
    v
[3] DOCUMENT_RECEIVED (audit)
    |
    v
[4] Language Detection
    |
    v
[5] AI Classification (4 categories, multi-label)
    |   AI_CLASSIFIED (audit)
    v
[6] Fact Extraction (category-specific)
    |   FACTS_EXTRACTED (audit)
    v
[7] Summary Generation
    |   SUMMARY_GENERATED (audit)
    v
[8] Human Review (accept/override)
    |   REVIEW_ACCEPTED / REVIEW_OVERRIDDEN (audit)
    v
Done
```

---

## 5. Tech Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| Angular | 21.2 | UI framework |
| TypeScript | 5.9 | Type safety |
| SCSS | - | Styling |
| Nginx | Alpine | Static serving + API proxy |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Java | 17 | Runtime |
| Spring Boot | 3.2.5 | REST API, DI, async processing |
| Spring Data JPA | - | ORM, database access |
| Spring WebFlux | - | WebClient for AI service calls |
| H2 Database | - | In-memory dev database |
| Oracle JDBC | 11 | Production database driver |
| Lombok | - | Boilerplate reduction |

### AI Service

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10 | Runtime |
| FastAPI | 0.110+ | REST API |
| Pydantic | 2.6+ | Data validation |
| Uvicorn | 0.29+ | ASGI server |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Multi-service orchestration |
| Nginx | Reverse proxy, static serving |

---

## 6. Project Structure

```
Smart-Inbox-Assistant-Healthcare/
├── frontend/                        # Angular application
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   └── dashboard/       # Main dashboard component
│   │   │   ├── models/              # TypeScript interfaces
│   │   │   └── services/            # HTTP services
│   │   └── styles.scss              # Global styles
│   ├── nginx.conf                   # Nginx configuration
│   ├── Dockerfile                   # Multi-stage Docker build
│   └── package.json                 # Dependencies
│
├── backend/                         # Spring Boot application
│   ├── src/main/java/com/clinicverse/inbox/
│   │   ├── controller/              # REST controllers
│   │   ├── service/                 # Business logic
│   │   ├── entity/                  # JPA entities
│   │   ├── dto/                     # Data transfer objects
│   │   ├── repository/              # Data access
│   │   ├── exception/               # Error handling
│   │   └── config/                  # Configuration
│   ├── src/main/resources/
│   │   ├── application.properties   # Configuration
│   │   ├── schema-oracle.sql        # Oracle DDL
│   │   └── data-oracle.sql          # Oracle seed data
│   ├── Dockerfile                   # Multi-stage Docker build
│   └── pom.xml                      # Maven dependencies
│
├── ai-service/                      # Python FastAPI application
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint
│   │   ├── api/                     # API routes
│   │   └── services/                # AI processing logic
│   │       ├── classifier.py        # Multi-category classifier
│   │       ├── icsr_extractor.py    # ICSR fact extraction
│   │       ├── extractors/          # Category-specific extractors
│   │       ├── summarizer.py        # Document summarization
│   │       ├── pdf_processor.py     # PDF pipeline
│   │       ├── ocr_service.py       # OCR processing
│   │       ├── llm/                 # LLM provider abstraction
│   │       └── batch_processor.py   # Batch processing
│   ├── tests/                       # 324 Python tests
│   ├── Dockerfile                   # Multi-stage Docker build
│   └── requirements.txt             # Python dependencies
│
├── database/                        # Database schemas
│   ├── schema.sql                   # H2 schema
│   ├── seed.sql                     # H2 seed data
│   ├── schema-oracle.sql            # Oracle DDL
│   ├── data-oracle.sql              # Oracle seed data
│   └── application-oracle.properties # Oracle config template
│
├── test-data/                       # Synthetic test data
│   ├── emails/                      # 10 sample emails
│   ├── pdfs/                        # 12 sample PDFs
│   └── manifest.json                # Test data index
│
├── sample-output/                   # Example AI results
│   └── batch-processing-report.json # Batch processing report
│
├── tests/                           # Integration tests
│   └── test_e2e_pipeline.py         # End-to-end pipeline test
│
├── docker-compose.yml               # Multi-service orchestration
├── .env.example                     # Environment variables template
├── test-report.json                 # Test execution report
└── README.md                        # This file
```

---

## 7. Prerequisites

### For Docker (Recommended)

- Docker Desktop 4.0+
- Docker Compose v2+
- 4 GB RAM allocated to Docker

### For Local Development

| Tool | Version | Purpose |
|------|---------|---------|
| Java | 17+ | Spring Boot backend |
| Maven | 3.8+ | Build Spring Boot |
| Node.js | 20+ | Angular frontend |
| npm | 10+ | Package management |
| Python | 3.10+ | AI service |
| pip | 22+ | Python packages |

### Optional

- Oracle Database 19c+ (for production)
- Tesseract OCR (for scanned PDF processing)

---

## 8. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### AI Service

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `LLM_PROVIDER` | `mock` | No | LLM provider: `mock`, `openai`, `anthropic` |
| `OPENAI_API_KEY` | - | If OpenAI | OpenAI API key |
| `ANTHROPIC_API_KEY` | - | If Anthropic | Anthropic API key |
| `LLM_MODEL` | `gpt-4o-mini` | No | Model name |
| `LLM_TEMPERATURE` | `0.3` | No | Sampling temperature |
| `LLM_MAX_TOKENS` | `4096` | No | Max response tokens |

### Backend

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DB_DRIVER` | `org.h2.Driver` | No | Database driver class |
| `DB_URL` | `jdbc:h2:mem:inboxdb` | No | JDBC URL |
| `DB_USERNAME` | `sa` | No | Database username |
| `DB_PASSWORD` | - | No | Database password |
| `DB_DIALECT` | `org.hibernate.dialect.H2Dialect` | No | JPA dialect |
| `DB_DDL_AUTO` | `create-drop` | No | Schema management |
| `AI_SERVICE_BASE_URL` | `http://localhost:8001` | No | AI service URL |

### IMAP Email

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `IMAP_HOST` | `imap.gmail.com` | Yes | IMAP server host |
| `IMAP_PORT` | `993` | Yes | IMAP server port |
| `IMAP_USERNAME` | - | Yes | Email address |
| `IMAP_PASSWORD` | - | Yes | App password |
| `IMAP_FOLDER` | `INBOX` | No | Mailbox folder |
| `IMAP_SSL` | `true` | No | Use SSL |

**Security:** Never commit `.env` to version control. The `.env.example` file contains only placeholder values.

---

## 9. Oracle Setup

### 1. Create Tablespace and User

```sql
CREATE TABLESPACE smart_inbox_data
  DATAFILE 'smart_inbox_data.dbf'
  SIZE 100M
  AUTOEXTEND ON;

CREATE USER smart_inbox
  IDENTIFIED BY your_password
  DEFAULT TABLESPACE smart_inbox_data
  QUOTA UNLIMITED ON smart_inbox_data;

GRANT CONNECT, RESOURCE TO smart_inbox;
GRANT CREATE SESSION TO smart_inbox;
GRANT CREATE TABLE TO smart_inbox;
GRANT CREATE SEQUENCE TO smart_inbox;
```

### 2. Run Schema

```bash
sqlplus smart_inbox/your_password@//your-host:1521/your-service @database/schema-oracle.sql
```

### 3. Configure Environment

```env
DB_DRIVER=oracle.jdbc.OracleDriver
DB_URL=jdbc:oracle:thin:@//your-oracle-host:1521/your-service-name
DB_USERNAME=smart_inbox
DB_PASSWORD=your_password
DB_DIALECT=org.hibernate.dialect.OracleDialect
DB_DDL_AUTO=validate
H2_CONSOLE_ENABLED=false
```

### 4. Oracle Driver

The `ojdbc11` driver is included in `pom.xml`. If you need to install it manually:

```bash
mvn install:install-file \
  -Dfile=ojdbc11.jar \
  -DgroupId=com.oracle.database.jdbc \
  -DartifactId=ojdbc11 \
  -Dversion=23.3.0.23.09 \
  -Dpackaging=jar
```

---

## 10. Python AI Service Setup

### Local Setup

```bash
cd ai-service

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Verify

```bash
curl http://localhost:8001/health
# {"status": "healthy", "version": "0.1.0"}
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/classify` | Classify document text |
| `POST` | `/api/v1/extract` | Extract structured facts |
| `POST` | `/api/v1/summarize` | Generate document summary |
| `POST` | `/api/v1/process` | Full processing pipeline |
| `POST` | `/api/v1/batch-process` | Batch process documents |

---

## 11. Spring Boot Setup

### Local Setup

```bash
cd backend

# Build
mvn clean package -DskipTests

# Run
mvn spring-boot:run

# Or run the JAR directly
java -jar target/inbox-backend-0.1.0-SNAPSHOT.jar
```

### Verify

```bash
curl http://localhost:8000/actuator/health
# {"status":"UP"}
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/emails` | List all emails |
| `GET` | `/api/emails/{id}` | Get email by ID |
| `POST` | `/api/emails` | Create new email |
| `GET` | `/api/emails/{id}/documents` | Get documents |
| `GET` | `/api/emails/{id}/classification` | Get classification |
| `GET` | `/api/emails/{id}/extraction` | Get extraction |
| `GET` | `/api/reviews` | List all reviews |
| `GET` | `/api/reviews/email/{emailId}` | Get review for email |
| `POST` | `/api/reviews/{emailId}/accept` | Accept classification |
| `POST` | `/api/reviews/{emailId}/override` | Override classification |
| `GET` | `/api/audit-logs` | List all audit logs |
| `GET` | `/api/audit-logs/email/{emailId}` | Get logs for email |
| `GET` | `/api/audit-logs/action/{action}` | Get logs by action |
| `GET` | `/api/audit-logs/stats` | Get audit statistics |

---

## 12. Angular Setup

### Local Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# The app runs at http://localhost:4000
# API calls are proxied to http://localhost:8000
```

### Build for Production

```bash
npm run build -- --configuration=production
# Output: dist/frontend/browser/
```

### Verify

Open http://localhost:4000 in your browser. The dashboard should display.

---

## 13. Email/IMAP Configuration

### Gmail Setup

1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an App Password for "Mail"
4. Use the 16-character password (no spaces)

```env
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USERNAME=your-email@gmail.com
IMAP_PASSWORD=your-16-char-app-password
IMAP_FOLDER=INBOX
IMAP_SSL=true
```

### Microsoft 365 Setup

```env
IMAP_HOST=outlook.office365.com
IMAP_PORT=993
IMAP_USERNAME=your-email@yourdomain.com
IMAP_PASSWORD=your-password
IMAP_FOLDER=INBOX
IMAP_SSL=true
```

### Custom IMAP Server

```env
IMAP_HOST=mail.yourdomain.com
IMAP_PORT=993
IMAP_USERNAME=user@yourdomain.com
IMAP_PASSWORD=your-password
IMAP_FOLDER=INBOX
IMAP_SSL=true
```

**Security:** Use environment variables or a secrets manager. Never hardcode credentials in source files or Docker images.

---

## 14. How to Run Locally

### Option A: Docker (Recommended)

```bash
# Clone and configure
git clone <repository-url>
cd Smart-Inbox-Assistant-Healthcare
cp .env.example .env

# Start all services
docker-compose up -d

# Access
# Frontend:     http://localhost
# Backend API:  http://localhost:8000
# AI Service:   http://localhost:8001
# H2 Console:   http://localhost:8000/h2-console
```

### Option B: Without Docker

Open three terminals:

**Terminal 1 - AI Service:**
```bash
cd ai-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8001
```

**Terminal 2 - Backend:**
```bash
cd backend
mvn spring-boot:run
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm install
npm start
```

---

## 15. Processing Test Emails

### Via API

```bash
# Create an email (triggers async AI processing)
curl -X POST http://localhost:8000/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "dr.smith@hospital.org",
    "recipient": "safety@clinicverse.com",
    "subject": "Patient Fall Report",
    "body": "Patient fell in Ward 3B at 02:30. No injuries. Bed rails were up."
  }'

# Response: {"id": 1, "status": "RECEIVED", "message": "Email received and processing queued"}

# Wait 2-3 seconds, then check results
curl http://localhost:8000/api/emails/1
curl http://localhost:8000/api/emails/1/classification
curl http://localhost:8000/api/emails/1/extraction
```

### Via Angular UI

1. Open http://localhost (or http://localhost:4000 for local dev)
2. The dashboard shows the email queue
3. Click an email to view classification, extraction, and audit history
4. Click "Accept" or "Override" to complete the review workflow

### Test Data Files

The `test-data/` directory contains 22 synthetic documents:

| Category | Files |
|----------|-------|
| Safety Reports | `email-01-safety-fall-report.txt`, `email-04-safety-device-recall.txt`, `email-08-safety-adverse-event.txt` |
| Quality Complaints | `email-02-quality-complaint.txt`, `email-06-quality-complaint-med-error.txt`, `email-09-quality-recall.txt` |
| Info Requests | `email-03-info-request.txt`, `email-05-info-request-research.txt` |
| Not Relevant | `email-07-marketing-irrelevant.txt` |
| Mixed | `email-10-mixed-multiple-topics.txt` |
| Digital PDFs | `pdfs/digital/digital-01` through `digital-05` |
| Scanned PDFs | `pdfs/scanned/scanned-01`, `scanned-02` |
| Non-English | `pdfs/non-english/non-english-01`, `non-english-02` |
| Articles | `pdfs/articles/article-01` through `article-05` |

---

## 16. Batch Processing

### Via API

```bash
curl -X POST http://localhost:8001/api/v1/batch-process \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "filename": "report-01.txt",
        "text": "Patient adverse event: allergic reaction to Penicillin.",
        "document_type": "email"
      },
      {
        "filename": "complaint-01.txt",
        "text": "Quality complaint: tablet coating peeling off.",
        "document_type": "email"
      }
    ]
  }'
```

### Via CLI Script

```bash
cd ai-service
python scripts/run_batch.py
```

### Report

Batch processing generates a report at `sample-output/batch-processing-report.json`:

```json
{
  "summary": {
    "total_documents": 24,
    "successful": 24,
    "failed": 0,
    "total_time_ms": 182.3,
    "average_time_ms": 7.4
  },
  "classification_counts": {
    "SAFETY_REPORT": 8,
    "QUALITY_COMPLAINT": 6,
    "INFO_REQUEST": 5,
    "NOT_RELEVANT": 5
  }
}
```

---

## 17. Running Tests

### Python Tests (324 tests)

```bash
cd ai-service
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=app --cov-report=html
```

**Test coverage:**

| Module | Tests | Description |
|--------|-------|-------------|
| `test_comprehensive.py` | 103 | Classification, extraction, summarization, integration |
| `test_pdf_comprehensive.py` | 38 | PDF extraction, OCR, language, tables, images |
| `test_classifier.py` | 43 | Multi-category classifier, edge cases |
| `test_icsr.py` | 44 | ICSR extraction, source references |
| `test_extractors.py` | 41 | Category-specific extractors |
| `test_llm.py` | 27 | LLM provider abstraction |
| `test_ocr.py` | 19 | OCR processing, uncertainty markers |
| `test_pdf_processing.py` | 30 | PDF pipeline, scanner detection |
| `test_summarizer.py` | 25 | Document summarization |

### Spring Boot Tests

```bash
cd backend
mvn test
```

### Angular Tests

```bash
cd frontend
npm test
```

### End-to-End Tests

```bash
# Start all services first
docker-compose up -d

cd tests
python -m pytest test_e2e_pipeline.py -v
```

---

## 18. Sample Outputs

### Classification Response

```json
{
  "primary_category": "SAFETY_REPORT",
  "primary_confidence": 0.95,
  "all_categories": [
    {"category": "SAFETY_REPORT", "confidence": 0.95},
    {"category": "QUALITY_COMPLAINT", "confidence": 0.15}
  ],
  "is_relevant": true,
  "relevance_confidence": 0.95,
  "summary": "Patient safety incident: fall in hospital ward."
}
```

### Extraction Response (ICSR)

```json
{
  "patient": {
    "value": {"name": "John Doe", "age": "72", "sex": "Male"},
    "confidence": 0.9,
    "source_ref": {"document_type": "email", "filename": "report.txt", "page": 1}
  },
  "drug": {
    "value": {"name": "Aspirin", "dose": "100mg"},
    "confidence": 0.85,
    "source_ref": {"document_type": "email", "filename": "report.txt", "page": 1}
  },
  "reaction": {
    "value": {"description": "Gastrointestinal bleeding"},
    "confidence": 0.8,
    "source_ref": {"document_type": "email", "filename": "report.txt", "page": 1}
  }
}
```

### Batch Processing Report

Located at `sample-output/batch-processing-report.json`:

```json
{
  "summary": {
    "total_documents": 24,
    "successful": 24,
    "failed": 0,
    "total_time_ms": 182.3,
    "average_time_ms": 7.4
  },
  "classification_counts": {
    "SAFETY_REPORT": 8,
    "QUALITY_COMPLAINT": 6,
    "INFO_REQUEST": 5,
    "NOT_RELEVANT": 5
  },
  "documents": [
    {
      "filename": "email-01-safety-fall-report.txt",
      "category": "SAFETY_REPORT",
      "confidence": 0.95,
      "processing_time_ms": 6.2
    }
  ]
}
```

---

## 19. Known Limitations

### AI Service

- **Mock LLM provider**: Default mode uses rule-based classification without actual LLM inference. Real LLM providers require API keys.
- **English-only rule-based classifier**: Non-English text is detected but classification rules are English-centric. LLM mode handles multilingual better.
- **OCR quality**: Tesseract OCR quality varies with scan resolution and document layout. Handwritten text is not reliably extracted.
- **PDF table extraction**: Basic table detection using layout heuristics. Complex multi-column layouts may not parse correctly.

### Backend

- **H2 in-memory database**: Data is lost on restart. Use Oracle for persistence.
- **No authentication**: API endpoints are open. Production requires auth middleware.
- **Single-instance async**: Processing uses a thread pool, not distributed queues.
- **No retry logic**: Failed AI service calls are logged but not retried.

### Frontend

- **No real-time updates**: Dashboard requires manual refresh. No WebSocket support.
- **No pagination**: Email list loads all records. Performance degrades at scale.
- **No file upload UI**: Emails must be created via API, not uploaded through the UI.

### General

- **Synthetic test data only**: No real patient information is used in testing.
- **No HIPAA compliance**: This is a prototype. Production requires encryption, access controls, and audit logging per HIPAA requirements.
- **No IMAP polling**: Email ingestion is triggered manually, not on a schedule.

---

## 20. AI/Data-Handling Trade-offs

### Rule-Based vs. LLM Classification

| Aspect | Rule-Based (Default) | LLM-Enhanced |
|--------|---------------------|--------------|
| **Speed** | ~7ms per document | ~2-5 seconds per document |
| **Cost** | Free | API costs per call |
| **Accuracy** | Good for known patterns | Better for nuanced text |
| **Multilingual** | English only | Multilingual |
| **Explainability** | High (keyword matches) | Low (black box) |
| **Customization** | Edit keyword banks | Prompt engineering |

**Decision:** Default to rule-based for speed and cost. Enable LLM mode for complex or multilingual documents via `LLM_PROVIDER=openai` or `LLM_PROVIDER=anthropic`.

### Missing Value Handling

The system never invents patient information. When a field is not found:

```json
{
  "value": "Not stated",
  "confidence": 0.0,
  "source_ref": {"document_type": "email", "filename": "report.txt", "page": 1}
}
```

**Trade-off:** This reduces extraction completeness but prevents false medical data from entering the system. A confidence threshold of 0.0 signals "not found" rather than "extracted with low confidence."

### Multi-Label Classification

Documents can match multiple categories independently:

```json
{
  "primary_category": "SAFETY_REPORT",
  "all_categories": [
    {"category": "SAFETY_REPORT", "confidence": 0.95},
    {"category": "QUALITY_COMPLAINT", "confidence": 0.30}
  ]
}
```

**Trade-off:** This increases recall (no missed categories) but may reduce precision. Reviewers see all matching categories and can override.

### OCR Uncertainty Markers

OCR text includes `[uncertain]` markers for low-confidence words:

```
The patient was administered [uncertain]aspirin[/uncertain] 100mg daily.
```

**Trade-off:** This signals OCR unreliability to downstream classifiers but adds noise to the text. The classifier treats `[uncertain]` text with lower weight.

---

## 21. Production Improvements

### Security

- [ ] Add OAuth2/OIDC authentication (Keycloak, Auth0)
- [ ] Implement role-based access control (RBAC)
- [ ] Enable HTTPS/TLS everywhere
- [ ] Add API rate limiting
- [ ] Implement HIPAA-compliant audit logging
- [ ] Encrypt data at rest and in transit
- [ ] Add secrets management (Vault, AWS Secrets Manager)

### Reliability

- [ ] Add message queue (RabbitMQ, Kafka) for email ingestion
- [ ] Implement retry logic with exponential backoff
- [ ] Add circuit breaker for AI service calls
- [ ] Implement dead letter queue for failed processing
- [ ] Add health check aggregation
- [ ] Implement distributed tracing (Jaeger, Zipkin)

### Scalability

- [ ] Horizontal scaling with Kubernetes
- [ ] Database connection pooling (HikariCP tuning)
- [ ] AI service auto-scaling based on queue depth
- [ ] CDN for frontend static assets
- [ ] Redis caching for classification results

### Observability

- [ ] Structured logging (JSON format)
- [ ] Prometheus metrics endpoint
- [ ] Grafana dashboards
- [ ] Alerting on processing failures
- [ ] Log aggregation (ELK stack)

### Data

- [ ] PostgreSQL or Oracle for persistent storage
- [ ] Database migrations (Flyway, Liquibase)
- [ ] Data backup and recovery procedures
- [ ] Data retention policies
- [ ] PII detection and masking

### AI/ML

- [ ] Fine-tuned classification model on domain data
- [ ] Active learning loop from reviewer overrides
- [ ] Model versioning and A/B testing
- [ ] Confidence calibration
- [ ] Document similarity search

### Frontend

- [ ] WebSocket for real-time updates
- [ ] Pagination and infinite scroll
- [ ] File upload UI for documents
- [ ] Advanced search and filtering
- [ ] Export to PDF/CSV
- [ ] Accessibility (WCAG 2.1 AA)


---

**Built with care for healthcare.**
