-- ============================================================================
-- Smart Inbox Assistant - Seed Data (Synthetic Only)
-- ============================================================================
-- All data is synthetic. No real patient information is stored.
-- ============================================================================

-- ============================================================================
-- EMAILS (10 synthetic emails across all categories)
-- ============================================================================

INSERT INTO email (id, subject, sender, recipient, body, received_at, status, created_at, updated_at)
VALUES (seq_email.NEXTVAL, 'URGENT: Patient Fall Incident Report - Ward 3B',
  'dr.elena.vasquez@meridian-general.org', 'safety-team@clinicverse.com',
  'A patient fall occurred in Ward 3B at 02:15 AM. The patient (synthetic ID: SYN-1042) slipped while attempting to use the restroom unassisted. No visible injuries observed. Bed alarm was activated but nurse response was delayed by 4 minutes.',
  TIMESTAMP '2025-08-12 09:15:00 +00:00', 'COMPLETED',
  TIMESTAMP '2025-08-12 09:16:00 +00:00', TIMESTAMP '2025-08-12 09:30:00 +00:00');

INSERT INTO email (id, subject, sender, recipient, body, received_at, status, created_at, updated_at)
VALUES (seq_email.NEXTVAL, 'Quality Complaint - Inconsistent Tablet Coating - Lot PC-2025-3391',
  'quality.dept@pharma-cure-labs.com', 'complaints@clinicverse.com',
  'We have received reports of inconsistent tablet coating on Lot PC-2025-3391. Dissolution testing shows 15% of tablets failing specification. Affected batch distributed to 12 pharmacies.',
  TIMESTAMP '2025-08-20 14:30:00 +00:00', 'COMPLETED',
  TIMESTAMP '2025-08-20 14:31:00 +00:00', TIMESTAMP '2025-08-20 15:00:00 +00:00');

INSERT INTO email (id, subject, sender, recipient, body, received_at, status, created_at, updated_at)
VALUES (seq_email.NEXTVAL, 'Information Request - Insulin Storage Requirements',
  'pharmacy.info@riverside-medical.org', 'support@clinicverse.com',
  'Could you please provide the storage requirements for insulin glargine products? Specifically, what is the recommended temperature range after opening, and how long can vials be stored at room temperature?',
  TIMESTAMP '2025-09-01 08:45:00 +00:00', 'COMPLETED',
  TIMESTAMP '2025-09-01 08:46:00 +00:00', TIMESTAMP '2025-09-01 09:00:00 +00:00');

INSERT INTO email (id, subject, sender, recipient, body, received_at, status, created_at, updated_at)
VALUES (seq_email.NEXTVAL, 'MedWatch Alert: Device Recall - Pulse Oximeter Model PX-500',
  'alerts@medwatch-systems.com', 'safety-team@clinicverse.com',
  'FDA Recall Class II: Pulse Oximeter Model PX-500, Serial numbers PX500-2024-0001 through PX500-2024-5000. Issue: Inaccurate SpO2 readings in patients with dark skin tones. Corrective action required within 30 days.',
  TIMESTAMP '2025-08-25 11:00:00 +00:00', 'COMPLETED',
  TIMESTAMP '2025-08-25 11:01:00 +00:00', TIMESTAMP '2025-08-25 11:30:00 +00:00');

INSERT INTO email (id, subject, sender, recipient, body, received_at, status, created_at, updated_at)
VALUES (seq_email.NEXTVAL, 'Question about research study enrollment criteria',
  'nora.kapoor@stanford.edu', 'support@clinicverse.com',
  'Hi, I am a research coordinator at Stanford. We are evaluating your platform for a new clinical trial. Can you tell me if your system supports custom classification categories beyond the standard four?',
  TIMESTAMP '2025-09-03 15:20:00 +00:00', 'COMPLETED',
  TIMESTAMP '2025-09-03 15:21:00 +00:00', TIMESTAMP '2025-09-03 15:45:00 +00:00');

INSERT INTO email (id, subject, sender, recipient, body, received_at, status, created_at, updated_at)
VALUES (seq_email.NEXTVAL, 'Complaint: Medication Dispensing Error',
  'james.omalley@cityhospital.org', 'complaints@clinicverse.com',
  'A medication dispensing error occurred on Ward 5A. Patient SYN-7823 was prescribed Metformin 500mg but received Metoprolol 50mg. The error was caught by the pharmacist before administration. Root cause: look-alike packaging.',
  TIMESTAMP '2025-08-18 10:45:00 +00:00', 'COMPLETED',
  TIMESTAMP '2025-08-18 10:46:00 +00:00', TIMESTAMP '2025-08-18 11:15:00 +00:00');

INSERT INTO email (id, subject, sender, recipient, body, received_at, status, created_at, updated_at)
VALUES (seq_email.NEXTVAL, 'Revolutionary AI-Powered Healthcare Management - Special Offer!',
  'marketing@healthtech-solutions.com', 'safety-team@clinicverse.com',
  'Transform your healthcare operations with our cutting-edge AI platform! Limited time offer: 40% off annual subscriptions. Schedule a demo today and receive a free consultation valued at $5,000.',
  TIMESTAMP '2025-09-05 09:00:00 +00:00', 'COMPLETED',
  TIMESTAMP '2025-09-05 09:01:00 +00:00', TIMESTAMP '2025-09-05 09:05:00 +00:00');

INSERT INTO email (id, subject, sender, recipient, body, received_at, status, created_at, updated_at)
VALUES (seq_email.NEXTVAL, 'Adverse Event Report - Anaphylaxis to Amoxicillin',
  'pharmacovigilance@globalpharma.com', 'safety-team@clinicverse.com',
  'ICSR Report: Patient SYN-5567, age 34, female, experienced anaphylactic shock 15 minutes after first dose of Amoxicillin 500mg. EpiPen administered. Patient stabilized. Hospitalized for 24-hour observation.',
  TIMESTAMP '2025-08-28 16:30:00 +00:00', 'COMPLETED',
  TIMESTAMP '2025-08-28 16:31:00 +00:00', TIMESTAMP '2025-08-28 17:00:00 +00:00');

INSERT INTO email (id, subject, sender, recipient, body, received_at, status, created_at, updated_at)
VALUES (seq_email.NEXTVAL, 'Product Recall Notice - Surgical Gloves',
  'supply.chain@medequip-solutions.com', 'complaints@clinicverse.com',
  'Recall Notice: Nitrile Examination Gloves, Lot SG-2025-1188. Particle contamination detected during QC testing. 5,000 boxes distributed. Please quarantine remaining stock and contact us for replacement.',
  TIMESTAMP '2025-09-02 13:15:00 +00:00', 'COMPLETED',
  TIMESTAMP '2025-09-02 13:16:00 +00:00', TIMESTAMP '2025-09-02 13:45:00 +00:00');

INSERT INTO email (id, subject, sender, recipient, body, received_at, status, created_at, updated_at)
VALUES (seq_email.NEXTVAL, 'Mixed inquiries - multiple topics',
  'office.manager@wellness-clinic.com', 'support@clinicverse.com',
  'Hello, I have several questions: 1) Our waiting room temperature has been too high - is there a complaint process? 2) Can you send me the latest storage guidelines for vaccines? 3) We are interested in upgrading our subscription plan.',
  TIMESTAMP '2025-09-04 11:30:00 +00:00', 'COMPLETED',
  TIMESTAMP '2025-09-04 11:31:00 +00:00', TIMESTAMP '2025-09-04 12:00:00 +00:00');

-- ============================================================================
-- DOCUMENTS (10 synthetic documents)
-- ============================================================================

INSERT INTO document (id, email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language)
VALUES (seq_document.NEXTVAL, 1, 'fall-incident-report.txt', 'text/plain', 2048,
  'Patient Fall Incident Report. Date: 2025-08-12. Location: Ward 3B, Room 312. Patient ID: SYN-1042. Time of incident: 02:15 AM. Description: Patient slipped while attempting to use restroom unassisted. Bed alarm activated. Nurse response time: 4 minutes. Injuries: None visible. Corrective actions: Bed alarm sensitivity reviewed, staff retraining scheduled.',
  0, 1, 'en');

INSERT INTO document (id, email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language)
VALUES (seq_document.NEXTVAL, 2, 'Inspection_Report_PC2025_3391.pdf', 'application/pdf', 156000,
  'Quality Inspection Report. Lot: PC-2025-3391. Product: Acetaminophen 500mg Tablets. Issue: Inconsistent coating thickness. Dissolution test: 15% out of specification. Root cause: Coating pan temperature fluctuation. Affected quantity: 50,000 tablets. Distribution: 12 pharmacies.',
  0, 3, 'en');

INSERT INTO document (id, email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language)
VALUES (seq_document.NEXTVAL, 3, 'insulin-storage-inquiry.txt', 'text/plain', 1024,
  'Information request regarding insulin glargine storage requirements. Questions: 1) Recommended temperature range after opening. 2) Room temperature storage duration. 3) Stability data availability.',
  0, 1, 'en');

INSERT INTO document (id, email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language)
VALUES (seq_document.NEXTVAL, 4, 'medwatch-recall-px500.txt', 'text/plain', 3072,
  'FDA MedWatch Alert. Device: Pulse Oximeter Model PX-500. Manufacturer: MedTech Sensors Inc. Serial Range: PX500-2024-0001 to PX500-2024-5000. Issue: Inaccurate SpO2 readings in patients with darker skin pigmentation. Risk: Delayed hypoxia detection. Classification: Class II Recall. Required action: Return affected units within 30 days.',
  0, 1, 'en');

INSERT INTO document (id, email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language)
VALUES (seq_document.NEXTVAL, 5, 'research-inquiry.txt', 'text/plain', 768,
  'Inquiry from Stanford research coordinator about platform capabilities for clinical trial support. Questions about custom classification categories.',
  0, 1, 'en');

INSERT INTO document (id, email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language)
VALUES (seq_document.NEXTVAL, 6, 'medication-error-report.pdf', 'application/pdf', 85000,
  'Medication Error Report. Ward: 5A. Patient: SYN-7823. Prescribed: Metformin 500mg. Dispensed: Metoprolol 50mg. Error caught by pharmacist. Root cause: Look-alike packaging between Metformin and Metoprolol. Corrective actions: Tall-man lettering added to labels, staff retraining on high-alert medications.',
  0, 2, 'en');

INSERT INTO document (id, email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language)
VALUES (seq_document.NEXTVAL, 7, 'marketing-flyer.txt', 'text/plain', 512,
  'Marketing content for AI healthcare management platform. Promotional offers and sales language.',
  0, 1, 'en');

INSERT INTO document (id, email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language)
VALUES (seq_document.NEXTVAL, 8, 'adverse-event-iccsr.pdf', 'application/pdf', 120000,
  'ICSR Report. Report ID: ICSR-2025-8834. Patient: SYN-5567, age 34, female. Drug: Amoxicillin 500mg. Event: Anaphylactic shock. Onset: 15 minutes post-first-dose. Treatment: EpiPen 0.3mg IM. Outcome: Stabilized, 24-hour observation. Causality: Probable.',
  0, 2, 'en');

INSERT INTO document (id, email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language)
VALUES (seq_document.NEXTVAL, 9, 'recall-notice-gloves.txt', 'text/plain', 1536,
  'Product Recall Notice. Product: Nitrile Examination Gloves. Lot: SG-2025-1188. Issue: Particle contamination detected. Quantity: 5,000 boxes. Distribution: Regional pharmacies. Action required: Quarantine and return.',
  0, 1, 'en');

INSERT INTO document (id, email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language)
VALUES (seq_document.NEXTVAL, 10, 'mixed-inquiries.txt', 'text/plain', 640,
  'Mixed content: complaint about waiting room temperature, information request about vaccine storage, and subscription upgrade inquiry.',
  0, 1, 'en');

-- ============================================================================
-- CLASSIFICATIONS (10 - one per email)
-- ============================================================================

INSERT INTO classification (id, email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence)
VALUES (seq_classification.NEXTVAL, 1, 'SAFETY_REPORT', 0.95,
  '[{"category":"SAFETY_REPORT","confidence":0.95,"reason":"Patient fall incident report"}]',
  'Patient fall incident in Ward 3B. No injuries. Bed alarm delayed response.', 1, 0.95);

INSERT INTO classification (id, email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence)
VALUES (seq_classification.NEXTVAL, 2, 'QUALITY_COMPLAINT', 0.92,
  '[{"category":"QUALITY_COMPLAINT","confidence":0.92,"reason":"Tablet coating inconsistency"}]',
  'Quality complaint about inconsistent tablet coating on Lot PC-2025-3391.', 1, 0.92);

INSERT INTO classification (id, email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence)
VALUES (seq_classification.NEXTVAL, 3, 'INFO_REQUEST', 0.88,
  '[{"category":"INFO_REQUEST","confidence":0.88,"reason":"Pharmacy requesting storage info"}]',
  'Pharmacy requesting insulin storage requirements.', 1, 0.88);

INSERT INTO classification (id, email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence)
VALUES (seq_classification.NEXTVAL, 4, 'SAFETY_REPORT', 0.94,
  '[{"category":"SAFETY_REPORT","confidence":0.94,"reason":"FDA device recall alert"}]',
  'FDA Class II recall of pulse oximeter for inaccurate readings.', 1, 0.94);

INSERT INTO classification (id, email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence)
VALUES (seq_classification.NEXTVAL, 5, 'INFO_REQUEST', 0.72,
  '[{"category":"INFO_REQUEST","confidence":0.72,"reason":"Research capability inquiry"}]',
  'Research coordinator inquiring about platform capabilities.', 1, 0.72);

INSERT INTO classification (id, email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence)
VALUES (seq_classification.NEXTVAL, 6, 'QUALITY_COMPLAINT', 0.85,
  '[{"category":"QUALITY_COMPLAINT","confidence":0.85,"reason":"Medication dispensing error"},{"category":"SAFETY_REPORT","confidence":0.70,"reason":"Patient safety event"}]',
  'Medication dispensing error caught by pharmacist. Root cause: look-alike packaging.', 1, 0.85);

INSERT INTO classification (id, email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence)
VALUES (seq_classification.NEXTVAL, 7, 'NOT_RELEVANT', 0.96,
  '[{"category":"NOT_RELEVANT","confidence":0.96,"reason":"Marketing email"}]',
  'Marketing email for healthcare software. Not relevant to safety/quality.', 0, 0.96);

INSERT INTO classification (id, email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence)
VALUES (seq_classification.NEXTVAL, 8, 'SAFETY_REPORT', 0.97,
  '[{"category":"SAFETY_REPORT","confidence":0.97,"reason":"Anaphylaxis adverse event"}]',
  'ICSR report for anaphylactic reaction to Amoxicillin.', 1, 0.97);

INSERT INTO classification (id, email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence)
VALUES (seq_classification.NEXTVAL, 9, 'QUALITY_COMPLAINT', 0.90,
  '[{"category":"QUALITY_COMPLAINT","confidence":0.90,"reason":"Surgical glove recall"}]',
  'Product recall for surgical gloves due to particle contamination.', 1, 0.90);

INSERT INTO classification (id, email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence)
VALUES (seq_classification.NEXTVAL, 10, 'QUALITY_COMPLAINT', 0.65,
  '[{"category":"QUALITY_COMPLAINT","confidence":0.65,"reason":"Temperature complaint"},{"category":"INFO_REQUEST","confidence":0.55,"reason":"Storage guidelines request"}]',
  'Mixed inquiries: temperature complaint, storage question, subscription inquiry.', 1, 0.65);

-- ============================================================================
-- EXTRACTED_FIELDS (25 fields across multiple emails)
-- ============================================================================

-- Email 1 (Fall Report) - ICSR-type fields
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 1, 'patient_id', 'SYN-1042', 0.90, 'document_text', 1, 'ICSR');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 1, 'incident_location', 'Ward 3B, Room 312', 0.95, 'document_text', 1, 'ICSR');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 1, 'incident_time', '02:15 AM', 0.88, 'document_text', 1, 'ICSR');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 1, 'injuries_observed', 'None visible', 0.85, 'document_text', 1, 'ICSR');

-- Email 2 (Quality Complaint) - Quality fields
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 2, 'lot_number', 'PC-2025-3391', 0.98, 'document_text', 1, 'QUALITY_COMPLAINT');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 2, 'product_name', 'Acetaminophen 500mg Tablets', 0.95, 'document_text', 1, 'QUALITY_COMPLAINT');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 2, 'defect_description', 'Inconsistent coating thickness', 0.92, 'document_text', 2, 'QUALITY_COMPLAINT');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 2, 'affected_quantity', '50000', 0.90, 'document_text', 2, 'QUALITY_COMPLAINT');

-- Email 3 (Info Request) - Request fields
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 3, 'product_topic', 'Insulin glargine', 0.88, 'document_text', 1, 'INFO_REQUEST');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 3, 'question_count', '3', 0.85, 'document_text', 1, 'INFO_REQUEST');

-- Email 4 (Recall) - Recall fields
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 4, 'device_name', 'Pulse Oximeter Model PX-500', 0.97, 'document_text', 1, 'SAFETY_REPORT');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 4, 'recall_class', 'Class II', 0.95, 'document_text', 1, 'SAFETY_REPORT');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 4, 'serial_range', 'PX500-2024-0001 to PX500-2024-5000', 0.94, 'document_text', 1, 'SAFETY_REPORT');

-- Email 6 (Medication Error) - Quality/Safety fields
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 6, 'patient_id', 'SYN-7823', 0.90, 'document_text', 1, 'QUALITY_COMPLAINT');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 6, 'prescribed_drug', 'Metformin 500mg', 0.95, 'document_text', 1, 'QUALITY_COMPLAINT');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 6, 'dispensed_drug', 'Metoprolol 50mg', 0.95, 'document_text', 1, 'QUALITY_COMPLAINT');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 6, 'root_cause', 'Look-alike packaging', 0.88, 'document_text', 2, 'QUALITY_COMPLAINT');

-- Email 8 (Adverse Event) - ICSR fields
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 8, 'report_id', 'ICSR-2025-8834', 0.98, 'document_text', 1, 'ICSR');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 8, 'patient_age', '34', 0.95, 'document_text', 1, 'ICSR');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 8, 'patient_sex', 'Female', 0.95, 'document_text', 1, 'ICSR');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 8, 'drug_name', 'Amoxicillin 500mg', 0.97, 'document_text', 1, 'ICSR');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 8, 'reaction', 'Anaphylactic shock', 0.97, 'document_text', 1, 'ICSR');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 8, 'onset_time', '15 minutes post-first-dose', 0.92, 'document_text', 1, 'ICSR');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 8, 'outcome', 'Stabilized, 24-hour observation', 0.90, 'document_text', 1, 'ICSR');

-- Email 9 (Recall) - Quality fields
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 9, 'lot_number', 'SG-2025-1188', 0.96, 'document_text', 1, 'QUALITY_COMPLAINT');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 9, 'product_name', 'Nitrile Examination Gloves', 0.94, 'document_text', 1, 'QUALITY_COMPLAINT');
INSERT INTO extracted_field (id, email_id, field_name, field_value, confidence, source_ref, source_page, extraction_type)
VALUES (seq_extracted_field.NEXTVAL, 9, 'defect_description', 'Particle contamination', 0.92, 'document_text', 1, 'QUALITY_COMPLAINT');

-- ============================================================================
-- TABLE_DATA (2 synthetic table extractions)
-- ============================================================================

-- Email 2 - Dissolution test results table
INSERT INTO table_data (id, email_id, document_id, table_index, page_number, headers, rows_data, row_count, column_count, description, confidence)
VALUES (seq_table_data.NEXTVAL, 2, 2, 0, 2,
  '["Sample ID","Dissolution %","Specification","Result"]',
  '[["S-001","82.3","NLT 80%","PASS"],["S-002","76.1","NLT 80%","FAIL"],["S-003","88.7","NLT 80%","PASS"],["S-004","71.2","NLT 80%","FAIL"],["S-005","85.9","NLT 80%","PASS"]]',
  5, 4, 'Dissolution test results for Lot PC-2025-3391', 0.90);

-- Email 6 - Corrective actions table
INSERT INTO table_data (id, email_id, document_id, table_index, page_number, headers, rows_data, row_count, column_count, description, confidence)
VALUES (seq_table_data.NEXTVAL, 6, 6, 0, 2,
  '["Action ID","Description","Owner","Due Date","Status"]',
  '[["CA-001","Add tall-man lettering to Metformin/Metoprolol labels","Pharmacy Director","2025-09-01","Completed"],["CA-002","Retrain Ward 5A staff on high-alert medications","Nurse Manager","2025-09-15","In Progress"],["CA-003","Update barcode scanning workflow","IT Lead","2025-10-01","Planned"]]',
  3, 5, 'Corrective actions for medication dispensing error', 0.88);

-- ============================================================================
-- IMAGE_DESCRIPTIONS (2 synthetic image descriptions)
-- ============================================================================

-- Email 8 - ICSR form diagram
INSERT INTO image_description (id, email_id, document_id, image_index, page_number, description, image_type, ocr_text, confidence)
VALUES (seq_image_description.NEXTVAL, 8, 8, 0, 1,
  'ICSR form header with manufacturer logo and report identification fields. Contains structured fields for patient demographics and adverse event classification.',
  'form_header', 'ICSR Report ID: ICSR-2025-8834 Manufacturer: Global Pharma Inc.', 0.88);

-- Email 2 - Defect photo
INSERT INTO image_description (id, email_id, document_id, image_index, page_number, description, image_type, ocr_text, confidence)
VALUES (seq_image_description.NEXTVAL, 2, 2, 0, 3,
  'Close-up photograph showing inconsistent tablet coating. Some tablets exhibit patchy coating with visible core material. Others show acceptable smooth coating.',
  'defect_photo', NULL, 0.85);

-- ============================================================================
-- REVIEWS (5 synthetic review actions)
-- ============================================================================

INSERT INTO review (id, email_id, reviewer_id, action, original_category, original_confidence, overridden_category, final_category, notes, reviewed_at)
VALUES (seq_review.NEXTVAL, 1, 'dr.smith', 'ACCEPTED', 'SAFETY_REPORT', 0.95, NULL, 'SAFETY_REPORT',
  'Confirmed as safety report. Corrective actions documented.', TIMESTAMP '2025-08-12 10:00:00 +00:00');

INSERT INTO review (id, email_id, reviewer_id, action, original_category, original_confidence, overridden_category, final_category, notes, reviewed_at)
VALUES (seq_review.NEXTVAL, 5, 'admin.chen', 'OVERRIDDEN', 'INFO_REQUEST', 0.72, 'NOT_RELEVANT', 'NOT_RELEVANT',
  'Research inquiry is not directly related to healthcare safety. Reclassified as NOT_RELEVANT.', TIMESTAMP '2025-09-03 16:30:00 +00:00');

INSERT INTO review (id, email_id, reviewer_id, action, original_category, original_confidence, overridden_category, final_category, notes, reviewed_at)
VALUES (seq_review.NEXTVAL, 6, 'dr.smith', 'ACCEPTED', 'QUALITY_COMPLAINT', 0.85, NULL, 'QUALITY_COMPLAINT',
  'Medication error confirmed as quality complaint. Safety team notified separately.', TIMESTAMP '2025-08-18 12:00:00 +00:00');

INSERT INTO review (id, email_id, reviewer_id, action, original_category, original_confidence, overridden_category, final_category, notes, reviewed_at)
VALUES (seq_review.NEXTVAL, 8, 'dr.patel', 'ACCEPTED', 'SAFETY_REPORT', 0.97, NULL, 'SAFETY_REPORT',
  'ICSR report verified. Forwarded to pharmacovigilance team.', TIMESTAMP '2025-08-28 17:30:00 +00:00');

INSERT INTO review (id, email_id, reviewer_id, action, original_category, original_confidence, overridden_category, final_category, notes, reviewed_at)
VALUES (seq_review.NEXTVAL, 10, 'admin.chen', 'OVERRIDDEN', 'QUALITY_COMPLAINT', 0.65, 'INFO_REQUEST', 'INFO_REQUEST',
  'Mixed content reclassified. Primary topic is information request about vaccine storage.', TIMESTAMP '2025-09-04 13:00:00 +00:00');

-- ============================================================================
-- AUDIT_LOG (20 synthetic audit events)
-- ============================================================================

INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 1, 'EMAIL_RECEIVED', 'imap', 'Email received from dr.elena.vasquez@meridian-general.org', 'imap', TIMESTAMP '2025-08-12 09:15:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 1, 'DOCUMENT_RECEIVED', 'system', 'PDF attachment: fall-incident-report.txt', 'system', TIMESTAMP '2025-08-12 09:16:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 1, 'AI_CLASSIFIED', 'ai-service', 'Classified as SAFETY_REPORT (confidence: 0.95)', 'ai-service', TIMESTAMP '2025-08-12 09:18:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 1, 'FACTS_EXTRACTED', 'ai-service', 'Extracted 4 fields (patient_id, incident_location, incident_time, injuries_observed)', 'ai-service', TIMESTAMP '2025-08-12 09:19:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 1, 'SUMMARY_GENERATED', 'ai-service', 'Summary generated (4 sentences)', 'ai-service', TIMESTAMP '2025-08-12 09:19:30 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 1, 'REVIEW_ACCEPTED', 'dr.smith', 'Accepted classification: SAFETY_REPORT', 'reviewer', TIMESTAMP '2025-08-12 10:00:00 +00:00');

INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 2, 'EMAIL_RECEIVED', 'imap', 'Email received from quality.dept@pharma-cure-labs.com', 'imap', TIMESTAMP '2025-08-20 14:30:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 2, 'DOCUMENT_RECEIVED', 'system', 'PDF attachment: Inspection_Report_PC2025_3391.pdf', 'system', TIMESTAMP '2025-08-20 14:31:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 2, 'AI_CLASSIFIED', 'ai-service', 'Classified as QUALITY_COMPLAINT (confidence: 0.92)', 'ai-service', TIMESTAMP '2025-08-20 14:33:00 +00:00');

INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 3, 'EMAIL_RECEIVED', 'imap', 'Email received from pharmacy.info@riverside-medical.org', 'imap', TIMESTAMP '2025-09-01 08:45:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 3, 'AI_CLASSIFIED', 'ai-service', 'Classified as INFO_REQUEST (confidence: 0.88)', 'ai-service', TIMESTAMP '2025-09-01 08:48:00 +00:00');

INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 5, 'EMAIL_RECEIVED', 'imap', 'Email received from nora.kapoor@stanford.edu', 'imap', TIMESTAMP '2025-09-03 15:20:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 5, 'AI_CLASSIFIED', 'ai-service', 'Classified as INFO_REQUEST (confidence: 0.72)', 'ai-service', TIMESTAMP '2025-09-03 15:22:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 5, 'REVIEW_OVERRIDDEN', 'admin.chen', 'Overridden from INFO_REQUEST to NOT_RELEVANT', 'reviewer', TIMESTAMP '2025-09-03 16:30:00 +00:00');

INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 7, 'EMAIL_RECEIVED', 'imap', 'Email received from marketing@healthtech-solutions.com', 'imap', TIMESTAMP '2025-09-05 09:00:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 7, 'AI_CLASSIFIED', 'ai-service', 'Classified as NOT_RELEVANT (confidence: 0.96)', 'ai-service', TIMESTAMP '2025-09-05 09:02:00 +00:00');

INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 8, 'EMAIL_RECEIVED', 'imap', 'Email received from pharmacovigilance@globalpharma.com', 'imap', TIMESTAMP '2025-08-28 16:30:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 8, 'AI_CLASSIFIED', 'ai-service', 'Classified as SAFETY_REPORT (confidence: 0.97)', 'ai-service', TIMESTAMP '2025-08-28 16:33:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 8, 'REVIEW_ACCEPTED', 'dr.patel', 'Accepted classification: SAFETY_REPORT', 'reviewer', TIMESTAMP '2025-08-28 17:30:00 +00:00');

INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 10, 'EMAIL_RECEIVED', 'imap', 'Email received from office.manager@wellness-clinic.com', 'imap', TIMESTAMP '2025-09-04 11:30:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 10, 'AI_CLASSIFIED', 'ai-service', 'Classified as QUALITY_COMPLAINT/INFO_REQUEST', 'ai-service', TIMESTAMP '2025-09-04 11:33:00 +00:00');
INSERT INTO audit_log (id, email_id, action, actor_id, details, source, timestamp)
VALUES (seq_audit_log.NEXTVAL, 10, 'REVIEW_OVERRIDDEN', 'admin.chen', 'Overridden from QUALITY_COMPLAINT to INFO_REQUEST', 'reviewer', TIMESTAMP '2025-09-04 13:00:00 +00:00');

-- ============================================================================
-- Verify seed data counts
-- ============================================================================
-- Emails:          10
-- Documents:       10
-- Classifications: 10
-- Extracted Fields: 25
-- Table Data:       2
-- Image Descriptions: 2
-- Reviews:          5
-- Audit Logs:      20
