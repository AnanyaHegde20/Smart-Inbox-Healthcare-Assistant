-- ============================================================================
-- Smart Inbox Assistant - Oracle Database Schema
-- ============================================================================
-- Healthcare email/document management system.
-- Supports: EMAIL, DOCUMENT, CLASSIFICATION, EXTRACTED_FIELD, TABLE_DATA,
--           IMAGE_DESCRIPTION, REVIEW, AUDIT_LOG
-- No real patient information is stored.
-- ============================================================================

-- Drop existing objects (in reverse dependency order)
BEGIN
  EXECUTE IMMEDIATE 'DROP TABLE audit_log CASCADE CONSTRAINTS';
  EXECUTE IMMEDIATE 'DROP TABLE review CASCADE CONSTRAINTS';
  EXECUTE IMMEDIATE 'DROP TABLE image_description CASCADE CONSTRAINTS';
  EXECUTE IMMEDIATE 'DROP TABLE table_data CASCADE CONSTRAINTS';
  EXECUTE IMMEDIATE 'DROP TABLE extracted_field CASCADE CONSTRAINTS';
  EXECUTE IMMEDIATE 'DROP TABLE classification CASCADE CONSTRAINTS';
  EXECUTE IMMEDIATE 'DROP TABLE document CASCADE CONSTRAINTS';
  EXECUTE IMMEDIATE 'DROP TABLE email CASCADE CONSTRAINTS';
EXCEPTION
  WHEN OTHERS THEN NULL;
END;
/

BEGIN
  EXECUTE IMMEDIATE 'DROP SEQUENCE seq_email';
  EXECUTE IMMEDIATE 'DROP SEQUENCE seq_document';
  EXECUTE IMMEDIATE 'DROP SEQUENCE seq_classification';
  EXECUTE IMMEDIATE 'DROP SEQUENCE seq_extracted_field';
  EXECUTE IMMEDIATE 'DROP SEQUENCE seq_table_data';
  EXECUTE IMMEDIATE 'DROP SEQUENCE seq_image_description';
  EXECUTE IMMEDIATE 'DROP SEQUENCE seq_review';
  EXECUTE IMMEDIATE 'DROP SEQUENCE seq_audit_log';
EXCEPTION
  WHEN OTHERS THEN NULL;
END;
/

-- ============================================================================
-- Sequences
-- ============================================================================

CREATE SEQUENCE seq_email          START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_document       START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_classification START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_extracted_field START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_table_data     START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_image_description START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_review         START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_audit_log      START WITH 1 INCREMENT BY 1 NOCACHE;

-- ============================================================================
-- 1. EMAIL - Core email metadata
-- ============================================================================

CREATE TABLE email (
  id             NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  subject        VARCHAR2(500)   NOT NULL,
  sender         VARCHAR2(255)   NOT NULL,
  recipient      VARCHAR2(255)   NOT NULL,
  body           CLOB,
  received_at    TIMESTAMP WITH TIME ZONE NOT NULL,
  status         VARCHAR2(20)    NOT NULL DEFAULT 'RECEIVED'
                   CHECK (status IN ('RECEIVED', 'PROCESSING', 'COMPLETED', 'FAILED')),
  ai_job_id      VARCHAR2(100),
  error_message  CLOB,
  created_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT SYSTIMESTAMP,
  updated_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT SYSTIMESTAMP
);

CREATE INDEX idx_email_status     ON email(status);
CREATE INDEX idx_email_received   ON email(received_at);
CREATE INDEX idx_email_sender     ON email(sender);

COMMENT ON TABLE  email IS 'Ingested email records from IMAP or manual entry';
COMMENT ON COLUMN email.status IS 'Processing lifecycle: RECEIVED -> PROCESSING -> COMPLETED/FAILED';

-- ============================================================================
-- 2. DOCUMENT - PDF and attachment metadata
-- ============================================================================

CREATE TABLE document (
  id              NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email_id        NUMBER          NOT NULL
                    REFERENCES email(id) ON DELETE CASCADE,
  filename        VARCHAR2(255)   NOT NULL,
  content_type    VARCHAR2(100),
  file_size       NUMBER,
  extracted_text  CLOB,
  ocr_used        NUMBER(1,0)     DEFAULT 0 CHECK (ocr_used IN (0, 1)),
  page_count      NUMBER,
  language        VARCHAR2(10),
  created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT SYSTIMESTAMP
);

CREATE INDEX idx_document_email ON document(email_id);

COMMENT ON TABLE  document IS 'PDF attachments and document metadata linked to emails';
COMMENT ON COLUMN document.ocr_used IS '0 = digital text extraction, 1 = OCR was applied';

-- ============================================================================
-- 3. CLASSIFICATION - AI classification results
-- ============================================================================

CREATE TABLE classification (
  id                    NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email_id              NUMBER          NOT NULL UNIQUE
                          REFERENCES email(id) ON DELETE CASCADE,
  primary_category      VARCHAR2(50)    NOT NULL
                          CHECK (primary_category IN (
                            'SAFETY_REPORT', 'QUALITY_COMPLAINT',
                            'INFO_REQUEST', 'NOT_RELEVANT'
                          )),
  primary_confidence    NUMBER(5,4)     NOT NULL
                          CHECK (primary_confidence BETWEEN 0 AND 1),
  all_categories        CLOB,
  summary               CLOB,
  is_relevant           NUMBER(1,0)
                          CHECK (is_relevant IN (0, 1)),
  relevance_confidence  NUMBER(5,4)
                          CHECK (relevance_confidence BETWEEN 0 AND 1),
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT SYSTIMESTAMP
);

CREATE INDEX idx_classification_category ON classification(primary_category);

COMMENT ON TABLE  classification IS 'Multi-label AI classification output per email';
COMMENT ON COLUMN classification.primary_category IS 'Highest-confidence category label';

-- ============================================================================
-- 4. EXTRACTED_FIELD - Individual extracted data fields
-- ============================================================================

CREATE TABLE extracted_field (
  id                NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email_id          NUMBER          NOT NULL
                      REFERENCES email(id) ON DELETE CASCADE,
  field_name        VARCHAR2(100)   NOT NULL,
  field_value       CLOB            NOT NULL,
  confidence        NUMBER(5,4)     NOT NULL
                      CHECK (confidence BETWEEN 0 AND 1),
  source_ref        VARCHAR2(255),
  source_page       NUMBER,
  extraction_type   VARCHAR2(50),
  created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT SYSTIMESTAMP
);

CREATE INDEX idx_extracted_field_email   ON extracted_field(email_id);
CREATE INDEX idx_extracted_field_name    ON extracted_field(field_name);
CREATE INDEX idx_extracted_field_type    ON extracted_field(extraction_type);

COMMENT ON TABLE  extracted_field IS 'Granular extracted fields with value, confidence, and source tracking';
COMMENT ON COLUMN extracted_field.source_ref IS 'Origin reference: document_type, filename, or text section';
COMMENT ON COLUMN extracted_field.source_page IS 'Page number where field was extracted (NULL if N/A)';

-- ============================================================================
-- 5. TABLE_DATA - Extracted tabular data from documents
-- ============================================================================

CREATE TABLE table_data (
  id                NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email_id          NUMBER          NOT NULL
                      REFERENCES email(id) ON DELETE CASCADE,
  document_id       NUMBER
                      REFERENCES document(id) ON DELETE SET NULL,
  table_index       NUMBER          NOT NULL DEFAULT 0,
  page_number       NUMBER,
  headers           CLOB,
  rows_data         CLOB,
  row_count         NUMBER,
  column_count      NUMBER,
  description       VARCHAR2(500),
  confidence        NUMBER(5,4)
                      CHECK (confidence BETWEEN 0 AND 1),
  created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT SYSTIMESTAMP
);

CREATE INDEX idx_table_data_email    ON table_data(email_id);
CREATE INDEX idx_table_data_document ON table_data(document_id);

COMMENT ON TABLE  table_data IS 'Structured tabular data extracted from PDF documents';

-- ============================================================================
-- 6. IMAGE_DESCRIPTION - AI-generated descriptions of images in documents
-- ============================================================================

CREATE TABLE image_description (
  id                NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email_id          NUMBER          NOT NULL
                      REFERENCES email(id) ON DELETE CASCADE,
  document_id       NUMBER
                      REFERENCES document(id) ON DELETE SET NULL,
  image_index       NUMBER          NOT NULL DEFAULT 0,
  page_number       NUMBER,
  description       CLOB            NOT NULL,
  image_type        VARCHAR2(50),
  ocr_text          CLOB,
  confidence        NUMBER(5,4)
                      CHECK (confidence BETWEEN 0 AND 1),
  created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT SYSTIMESTAMP
);

CREATE INDEX idx_image_desc_email    ON image_description(email_id);
CREATE INDEX idx_image_desc_document ON image_description(document_id);

COMMENT ON TABLE  image_description IS 'AI-generated descriptions and OCR for images embedded in documents';

-- ============================================================================
-- 7. REVIEW - Human reviewer actions
-- ============================================================================

CREATE TABLE review (
  id                  NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email_id            NUMBER          NOT NULL UNIQUE
                        REFERENCES email(id) ON DELETE CASCADE,
  reviewer_id         VARCHAR2(100)   NOT NULL,
  action              VARCHAR2(20)    NOT NULL
                        CHECK (action IN ('ACCEPTED', 'OVERRIDDEN')),
  original_category   VARCHAR2(50),
  original_confidence NUMBER(5,4)
                        CHECK (original_confidence BETWEEN 0 AND 1),
  overridden_category VARCHAR2(50),
  final_category      VARCHAR2(50),
  notes               CLOB,
  reviewed_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT SYSTIMESTAMP
);

CREATE INDEX idx_review_email     ON review(email_id);
CREATE INDEX idx_review_reviewer  ON review(reviewer_id);

COMMENT ON TABLE  review IS 'Human review actions: accept or override AI classification';

-- ============================================================================
-- 8. AUDIT_LOG - Complete event trail
-- ============================================================================

CREATE TABLE audit_log (
  id          NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email_id    NUMBER,
  action      VARCHAR2(50)    NOT NULL,
  actor_id    VARCHAR2(100),
  details     CLOB,
  source      VARCHAR2(50),
  timestamp   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT SYSTIMESTAMP
);

CREATE INDEX idx_audit_email     ON audit_log(email_id);
CREATE INDEX idx_audit_action    ON audit_log(action);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);

COMMENT ON TABLE  audit_log IS 'Immutable audit trail for all system events';
