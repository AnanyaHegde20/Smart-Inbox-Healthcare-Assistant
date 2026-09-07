-- ============================================================
-- Smart Inbox Assistant - H2 Seed Data
-- ============================================================
-- Synthetic data only. No real patient information.
-- Auto-loaded by Spring Boot on startup.
-- ============================================================

-- ============================================================
-- EMAILS (10 synthetic emails across all categories)
-- ============================================================

INSERT INTO emails (subject, sender, recipient, body, received_at, status, created_at, updated_at) VALUES
('URGENT: Patient Fall Incident Report - Ward 3B', 'dr.elena.vasquez@meridian-general.org', 'safety-team@clinicverse.com',
 'A patient fall occurred in Ward 3B at 02:15 AM. The patient (synthetic ID: SYN-1042) slipped while attempting to use the restroom unassisted. No visible injuries observed. Bed alarm was activated but nurse response was delayed by 4 minutes.',
 TIMESTAMP '2025-08-12 09:15:00+00:00', 'COMPLETED', TIMESTAMP '2025-08-12 09:16:00+00:00', TIMESTAMP '2025-08-12 09:30:00+00:00');

INSERT INTO emails (subject, sender, recipient, body, received_at, status, created_at, updated_at) VALUES
('Quality Complaint - Inconsistent Tablet Coating - Lot PC-2025-3391', 'quality.dept@pharma-cure-labs.com', 'complaints@clinicverse.com',
 'We have received reports of inconsistent tablet coating on Lot PC-2025-3391. Dissolution testing shows 15% of tablets failing specification. Affected batch distributed to 12 pharmacies.',
 TIMESTAMP '2025-08-20 14:30:00+00:00', 'COMPLETED', TIMESTAMP '2025-08-20 14:31:00+00:00', TIMESTAMP '2025-08-20 15:00:00+00:00');

INSERT INTO emails (subject, sender, recipient, body, received_at, status, created_at, updated_at) VALUES
('Information Request - Insulin Storage Requirements', 'pharmacy.info@riverside-medical.org', 'support@clinicverse.com',
 'Could you please provide the storage requirements for insulin glargine products? Specifically, what is the recommended temperature range after opening, and how long can vials be stored at room temperature?',
 TIMESTAMP '2025-09-01 08:45:00+00:00', 'COMPLETED', TIMESTAMP '2025-09-01 08:46:00+00:00', TIMESTAMP '2025-09-01 09:00:00+00:00');

INSERT INTO emails (subject, sender, recipient, body, received_at, status, created_at, updated_at) VALUES
('MedWatch Alert: Device Recall - Pulse Oximeter Model PX-500', 'alerts@medwatch-systems.com', 'safety-team@clinicverse.com',
 'FDA Recall Class II: Pulse Oximeter Model PX-500, Serial numbers PX500-2024-0001 through PX500-2024-5000. Issue: Inaccurate SpO2 readings in patients with dark skin tones. Corrective action required within 30 days.',
 TIMESTAMP '2025-08-25 11:00:00+00:00', 'COMPLETED', TIMESTAMP '2025-08-25 11:01:00+00:00', TIMESTAMP '2025-08-25 11:30:00+00:00');

INSERT INTO emails (subject, sender, recipient, body, received_at, status, created_at, updated_at) VALUES
('Question about research study enrollment criteria', 'nora.kapoor@stanford.edu', 'support@clinicverse.com',
 'Hi, I am a research coordinator at Stanford. We are evaluating your platform for a new clinical trial. Can you tell me if your system supports custom classification categories beyond the standard four?',
 TIMESTAMP '2025-09-03 15:20:00+00:00', 'COMPLETED', TIMESTAMP '2025-09-03 15:21:00+00:00', TIMESTAMP '2025-09-03 15:45:00+00:00');

INSERT INTO emails (subject, sender, recipient, body, received_at, status, created_at, updated_at) VALUES
('Complaint: Medication Dispensing Error', 'james.omalley@cityhospital.org', 'complaints@clinicverse.com',
 'A medication dispensing error occurred on Ward 5A. Patient SYN-7823 was prescribed Metformin 500mg but received Metoprolol 50mg. The error was caught by the pharmacist before administration. Root cause: look-alike packaging.',
 TIMESTAMP '2025-08-18 10:45:00+00:00', 'COMPLETED', TIMESTAMP '2025-08-18 10:46:00+00:00', TIMESTAMP '2025-08-18 11:15:00+00:00');

INSERT INTO emails (subject, sender, recipient, body, received_at, status, created_at, updated_at) VALUES
('Revolutionary AI-Powered Healthcare Management - Special Offer!', 'marketing@healthtech-solutions.com', 'safety-team@clinicverse.com',
 'Transform your healthcare operations with our cutting-edge AI platform! Limited time offer: 40% off annual subscriptions. Schedule a demo today and receive a free consultation valued at $5,000.',
 TIMESTAMP '2025-09-05 09:00:00+00:00', 'COMPLETED', TIMESTAMP '2025-09-05 09:01:00+00:00', TIMESTAMP '2025-09-05 09:05:00+00:00');

INSERT INTO emails (subject, sender, recipient, body, received_at, status, created_at, updated_at) VALUES
('Adverse Event Report - Anaphylaxis to Amoxicillin', 'pharmacovigilance@globalpharma.com', 'safety-team@clinicverse.com',
 'ICSR Report: Patient SYN-5567, age 34, female, experienced anaphylactic shock 15 minutes after first dose of Amoxicillin 500mg. EpiPen administered. Patient stabilized. Hospitalized for 24-hour observation.',
 TIMESTAMP '2025-08-28 16:30:00+00:00', 'COMPLETED', TIMESTAMP '2025-08-28 16:31:00+00:00', TIMESTAMP '2025-08-28 17:00:00+00:00');

INSERT INTO emails (subject, sender, recipient, body, received_at, status, created_at, updated_at) VALUES
('Product Recall Notice - Surgical Gloves', 'supply.chain@medequip-solutions.com', 'complaints@clinicverse.com',
 'Recall Notice: Nitrile Examination Gloves, Lot SG-2025-1188. Particle contamination detected during QC testing. 5,000 boxes distributed. Please quarantine remaining stock and contact us for replacement.',
 TIMESTAMP '2025-09-02 13:15:00+00:00', 'COMPLETED', TIMESTAMP '2025-09-02 13:16:00+00:00', TIMESTAMP '2025-09-02 13:45:00+00:00');

INSERT INTO emails (subject, sender, recipient, body, received_at, status, created_at, updated_at) VALUES
('Mixed inquiries - multiple topics', 'office.manager@wellness-clinic.com', 'support@clinicverse.com',
 'Hello, I have several questions: 1) Our waiting room temperature has been too high - is there a complaint process? 2) Can you send me the latest storage guidelines for vaccines? 3) We are interested in upgrading our subscription plan.',
 TIMESTAMP '2025-09-04 11:30:00+00:00', 'COMPLETED', TIMESTAMP '2025-09-04 11:31:00+00:00', TIMESTAMP '2025-09-04 12:00:00+00:00');

-- ============================================================
-- DOCUMENTS (10 synthetic documents, one per email)
-- ============================================================

INSERT INTO documents (email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language) VALUES
(1, 'fall-incident-report.txt', 'text/plain', 2048,
 'Patient Fall Incident Report. Date: 2025-08-12. Location: Ward 3B, Room 312. Patient ID: SYN-1042. Time of incident: 02:15 AM. Description: Patient slipped while attempting to use restroom unassisted. Bed alarm activated. Nurse response time: 4 minutes. Injuries: None visible. Corrective actions: Bed alarm sensitivity reviewed, staff retraining scheduled.',
 false, 1, 'en');

INSERT INTO documents (email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language) VALUES
(2, 'Inspection_Report_PC2025_3391.pdf', 'application/pdf', 156000,
 'Quality Inspection Report. Lot: PC-2025-3391. Product: Acetaminophen 500mg Tablets. Issue: Inconsistent coating thickness. Dissolution test: 15% out of specification. Root cause: Coating pan temperature fluctuation. Affected quantity: 50,000 tablets. Distribution: 12 pharmacies.',
 false, 3, 'en');

INSERT INTO documents (email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language) VALUES
(3, 'insulin-storage-inquiry.txt', 'text/plain', 1024,
 'Information request regarding insulin glargine storage requirements. Questions: 1) Recommended temperature range after opening. 2) Room temperature storage duration. 3) Stability data availability.',
 false, 1, 'en');

INSERT INTO documents (email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language) VALUES
(4, 'medwatch-recall-px500.txt', 'text/plain', 3072,
 'FDA MedWatch Alert. Device: Pulse Oximeter Model PX-500. Manufacturer: MedTech Sensors Inc. Serial Range: PX500-2024-0001 to PX500-2024-5000. Issue: Inaccurate SpO2 readings in patients with darker skin pigmentation. Risk: Delayed hypoxia detection. Classification: Class II Recall. Required action: Return affected units within 30 days.',
 false, 1, 'en');

INSERT INTO documents (email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language) VALUES
(5, 'research-inquiry.txt', 'text/plain', 768,
 'Inquiry from Stanford research coordinator about platform capabilities for clinical trial support. Questions about custom classification categories.',
 false, 1, 'en');

INSERT INTO documents (email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language) VALUES
(6, 'medication-error-report.pdf', 'application/pdf', 85000,
 'Medication Error Report. Ward: 5A. Patient: SYN-7823. Prescribed: Metformin 500mg. Dispensed: Metoprolol 50mg. Error caught by pharmacist. Root cause: Look-alike packaging between Metformin and Metoprolol. Corrective actions: Tall-man lettering added to labels, staff retraining on high-alert medications.',
 false, 2, 'en');

INSERT INTO documents (email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language) VALUES
(7, 'marketing-flyer.txt', 'text/plain', 512,
 'Marketing content for AI healthcare management platform. Promotional offers and sales language.',
 false, 1, 'en');

INSERT INTO documents (email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language) VALUES
(8, 'adverse-event-iccsr.pdf', 'application/pdf', 120000,
 'ICSR Report. Report ID: ICSR-2025-8834. Patient: SYN-5567, age 34, female. Drug: Amoxicillin 500mg. Event: Anaphylactic shock. Onset: 15 minutes post-first-dose. Treatment: EpiPen 0.3mg IM. Outcome: Stabilized, 24-hour observation. Causality: Probable.',
 false, 2, 'en');

INSERT INTO documents (email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language) VALUES
(9, 'recall-notice-gloves.txt', 'text/plain', 1536,
 'Product Recall Notice. Product: Nitrile Examination Gloves. Lot: SG-2025-1188. Issue: Particle contamination detected. Quantity: 5,000 boxes. Distribution: Regional pharmacies. Action required: Quarantine and return.',
 false, 1, 'en');

INSERT INTO documents (email_id, filename, content_type, file_size, extracted_text, ocr_used, page_count, language) VALUES
(10, 'mixed-inquiries.txt', 'text/plain', 640,
 'Mixed content: complaint about waiting room temperature, information request about vaccine storage, and subscription upgrade inquiry.',
 false, 1, 'en');

-- ============================================================
-- CLASSIFICATIONS (10 - one per email)
-- ============================================================

INSERT INTO classifications (email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence, created_at) VALUES
(1, 'SAFETY_REPORT', 0.95,
 '[{"category":"SAFETY_REPORT","confidence":0.95,"reason":"Patient fall incident report"}]',
 'Patient fall incident in Ward 3B. No injuries. Bed alarm delayed response.', true, 0.95, TIMESTAMP '2025-08-12 09:18:00+00:00');

INSERT INTO classifications (email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence, created_at) VALUES
(2, 'QUALITY_COMPLAINT', 0.92,
 '[{"category":"QUALITY_COMPLAINT","confidence":0.92,"reason":"Tablet coating inconsistency"}]',
 'Quality complaint about inconsistent tablet coating on Lot PC-2025-3391.', true, 0.92, TIMESTAMP '2025-08-20 14:33:00+00:00');

INSERT INTO classifications (email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence, created_at) VALUES
(3, 'INFO_REQUEST', 0.88,
 '[{"category":"INFO_REQUEST","confidence":0.88,"reason":"Pharmacy requesting storage info"}]',
 'Pharmacy requesting insulin storage requirements.', true, 0.88, TIMESTAMP '2025-09-01 08:48:00+00:00');

INSERT INTO classifications (email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence, created_at) VALUES
(4, 'SAFETY_REPORT', 0.94,
 '[{"category":"SAFETY_REPORT","confidence":0.94,"reason":"FDA device recall alert"}]',
 'FDA Class II recall of pulse oximeter for inaccurate readings.', true, 0.94, TIMESTAMP '2025-08-25 11:03:00+00:00');

INSERT INTO classifications (email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence, created_at) VALUES
(5, 'INFO_REQUEST', 0.72,
 '[{"category":"INFO_REQUEST","confidence":0.72,"reason":"Research capability inquiry"}]',
 'Research coordinator inquiring about platform capabilities.', true, 0.72, TIMESTAMP '2025-09-03 15:22:00+00:00');

INSERT INTO classifications (email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence, created_at) VALUES
(6, 'QUALITY_COMPLAINT', 0.85,
 '[{"category":"QUALITY_COMPLAINT","confidence":0.85,"reason":"Medication dispensing error"},{"category":"SAFETY_REPORT","confidence":0.70,"reason":"Patient safety event"}]',
 'Medication dispensing error caught by pharmacist. Root cause: look-alike packaging.', true, 0.85, TIMESTAMP '2025-08-18 10:48:00+00:00');

INSERT INTO classifications (email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence, created_at) VALUES
(7, 'NOT_RELEVANT', 0.96,
 '[{"category":"NOT_RELEVANT","confidence":0.96,"reason":"Marketing email"}]',
 'Marketing email for healthcare software. Not relevant to safety/quality.', false, 0.96, TIMESTAMP '2025-09-05 09:02:00+00:00');

INSERT INTO classifications (email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence, created_at) VALUES
(8, 'SAFETY_REPORT', 0.97,
 '[{"category":"SAFETY_REPORT","confidence":0.97,"reason":"Anaphylaxis adverse event"}]',
 'ICSR report for anaphylactic reaction to Amoxicillin.', true, 0.97, TIMESTAMP '2025-08-28 16:33:00+00:00');

INSERT INTO classifications (email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence, created_at) VALUES
(9, 'QUALITY_COMPLAINT', 0.90,
 '[{"category":"QUALITY_COMPLAINT","confidence":0.90,"reason":"Surgical glove recall"}]',
 'Product recall for surgical gloves due to particle contamination.', true, 0.90, TIMESTAMP '2025-09-02 13:18:00+00:00');

INSERT INTO classifications (email_id, primary_category, primary_confidence, all_categories, summary, is_relevant, relevance_confidence, created_at) VALUES
(10, 'QUALITY_COMPLAINT', 0.65,
 '[{"category":"QUALITY_COMPLAINT","confidence":0.65,"reason":"Temperature complaint"},{"category":"INFO_REQUEST","confidence":0.55,"reason":"Storage guidelines request"}]',
 'Mixed inquiries: temperature complaint, storage question, subscription inquiry.', true, 0.65, TIMESTAMP '2025-09-04 11:33:00+00:00');

-- ============================================================
-- EXTRACTED FIELDS (extracted_data as JSON per email)
-- ============================================================

INSERT INTO extractions (email_id, extracted_data, extraction_type, confidence_score, created_at) VALUES
(1, '{"patient_id":"SYN-1042","incident_location":"Ward 3B, Room 312","incident_time":"02:15 AM","injuries_observed":"None visible"}', 'ICSR', 0.90, TIMESTAMP '2025-08-12 09:19:00+00:00');

INSERT INTO extractions (email_id, extracted_data, extraction_type, confidence_score, created_at) VALUES
(2, '{"lot_number":"PC-2025-3391","product_name":"Acetaminophen 500mg Tablets","defect_description":"Inconsistent coating thickness","affected_quantity":"50000"}', 'QUALITY_COMPLAINT', 0.92, TIMESTAMP '2025-08-20 14:34:00+00:00');

INSERT INTO extractions (email_id, extracted_data, extraction_type, confidence_score, created_at) VALUES
(3, '{"product_topic":"Insulin glargine","question_count":"3","questions":["Temperature range after opening","Room temperature duration","Stability data"]}', 'INFO_REQUEST', 0.88, TIMESTAMP '2025-09-01 08:49:00+00:00');

INSERT INTO extractions (email_id, extracted_data, extraction_type, confidence_score, created_at) VALUES
(4, '{"device_name":"Pulse Oximeter Model PX-500","recall_class":"Class II","serial_range":"PX500-2024-0001 to PX500-2024-5000","manufacturer":"MedTech Sensors Inc"}', 'SAFETY_REPORT', 0.94, TIMESTAMP '2025-08-25 11:04:00+00:00');

INSERT INTO extractions (email_id, extracted_data, extraction_type, confidence_score, created_at) VALUES
(5, '{"institution":"Stanford","role":"Research Coordinator","inquiry":"Custom classification categories"}', 'INFO_REQUEST', 0.72, TIMESTAMP '2025-09-03 15:23:00+00:00');

INSERT INTO extractions (email_id, extracted_data, extraction_type, confidence_score, created_at) VALUES
(6, '{"patient_id":"SYN-7823","prescribed_drug":"Metformin 500mg","dispensed_drug":"Metoprolol 50mg","root_cause":"Look-alike packaging"}', 'QUALITY_COMPLAINT', 0.85, TIMESTAMP '2025-08-18 10:49:00+00:00');

INSERT INTO extractions (email_id, extracted_data, extraction_type, confidence_score, created_at) VALUES
(7, '{"type":"marketing","offer":"40% off annual subscriptions","company":"HealthTech Solutions"}', 'NOT_RELEVANT', 0.96, TIMESTAMP '2025-09-05 09:03:00+00:00');

INSERT INTO extractions (email_id, extracted_data, extraction_type, confidence_score, created_at) VALUES
(8, '{"report_id":"ICSR-2025-8834","patient_age":"34","patient_sex":"Female","drug_name":"Amoxicillin 500mg","reaction":"Anaphylactic shock","onset_time":"15 minutes post-first-dose","outcome":"Stabilized, 24-hour observation"}', 'ICSR', 0.97, TIMESTAMP '2025-08-28 16:34:00+00:00');

INSERT INTO extractions (email_id, extracted_data, extraction_type, confidence_score, created_at) VALUES
(9, '{"lot_number":"SG-2025-1188","product_name":"Nitrile Examination Gloves","defect_description":"Particle contamination","affected_quantity":"5000"}', 'QUALITY_COMPLAINT', 0.90, TIMESTAMP '2025-09-02 13:19:00+00:00');

INSERT INTO extractions (email_id, extracted_data, extraction_type, confidence_score, created_at) VALUES
(10, '{"topics":["temperature complaint","vaccine storage","subscription upgrade"],"primary_topic":"Mixed inquiries"}', 'QUALITY_COMPLAINT', 0.65, TIMESTAMP '2025-09-04 11:34:00+00:00');

-- ============================================================
-- REVIEWS (5 synthetic review actions)
-- ============================================================

INSERT INTO reviews (email_id, reviewer_id, action, original_category, original_confidence, overridden_category, final_category, notes, reviewed_at) VALUES
(1, 'dr.smith', 'ACCEPTED', 'SAFETY_REPORT', 0.95, NULL, 'SAFETY_REPORT',
 'Confirmed as safety report. Corrective actions documented.', TIMESTAMP '2025-08-12 10:00:00+00:00');

INSERT INTO reviews (email_id, reviewer_id, action, original_category, original_confidence, overridden_category, final_category, notes, reviewed_at) VALUES
(5, 'admin.chen', 'OVERRIDDEN', 'INFO_REQUEST', 0.72, 'NOT_RELEVANT', 'NOT_RELEVANT',
 'Research inquiry is not directly related to healthcare safety. Reclassified as NOT_RELEVANT.', TIMESTAMP '2025-09-03 16:30:00+00:00');

INSERT INTO reviews (email_id, reviewer_id, action, original_category, original_confidence, overridden_category, final_category, notes, reviewed_at) VALUES
(6, 'dr.smith', 'ACCEPTED', 'QUALITY_COMPLAINT', 0.85, NULL, 'QUALITY_COMPLAINT',
 'Medication error confirmed as quality complaint. Safety team notified separately.', TIMESTAMP '2025-08-18 12:00:00+00:00');

INSERT INTO reviews (email_id, reviewer_id, action, original_category, original_confidence, overridden_category, final_category, notes, reviewed_at) VALUES
(8, 'dr.patel', 'ACCEPTED', 'SAFETY_REPORT', 0.97, NULL, 'SAFETY_REPORT',
 'ICSR report verified. Forwarded to pharmacovigilance team.', TIMESTAMP '2025-08-28 17:30:00+00:00');

INSERT INTO reviews (email_id, reviewer_id, action, original_category, original_confidence, overridden_category, final_category, notes, reviewed_at) VALUES
(10, 'admin.chen', 'OVERRIDDEN', 'QUALITY_COMPLAINT', 0.65, 'INFO_REQUEST', 'INFO_REQUEST',
 'Mixed content reclassified. Primary topic is information request about vaccine storage.', TIMESTAMP '2025-09-04 13:00:00+00:00');

-- ============================================================
-- AUDIT LOGS (30 synthetic audit events)
-- ============================================================

INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(1, 'EMAIL_RECEIVED', 'system', 'Email received from dr.elena.vasquez@meridian-general.org', TIMESTAMP '2025-08-12 09:15:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(1, 'DOCUMENT_RECEIVED', 'system', 'Document attached: fall-incident-report.txt', TIMESTAMP '2025-08-12 09:16:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(1, 'AI_CLASSIFIED', 'ai-service', 'Classified as SAFETY_REPORT (confidence: 0.95)', TIMESTAMP '2025-08-12 09:18:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(1, 'FACTS_EXTRACTED', 'ai-service', 'Extracted 4 fields (patient_id, incident_location, incident_time, injuries_observed)', TIMESTAMP '2025-08-12 09:19:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(1, 'SUMMARY_GENERATED', 'ai-service', 'Summary generated', TIMESTAMP '2025-08-12 09:19:30+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(1, 'REVIEW_ACCEPTED', 'dr.smith', 'Accepted classification: SAFETY_REPORT', TIMESTAMP '2025-08-12 10:00:00+00:00');

INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(2, 'EMAIL_RECEIVED', 'system', 'Email received from quality.dept@pharma-cure-labs.com', TIMESTAMP '2025-08-20 14:30:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(2, 'DOCUMENT_RECEIVED', 'system', 'Document attached: Inspection_Report_PC2025_3391.pdf', TIMESTAMP '2025-08-20 14:31:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(2, 'AI_CLASSIFIED', 'ai-service', 'Classified as QUALITY_COMPLAINT (confidence: 0.92)', TIMESTAMP '2025-08-20 14:33:00+00:00');

INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(3, 'EMAIL_RECEIVED', 'system', 'Email received from pharmacy.info@riverside-medical.org', TIMESTAMP '2025-09-01 08:45:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(3, 'AI_CLASSIFIED', 'ai-service', 'Classified as INFO_REQUEST (confidence: 0.88)', TIMESTAMP '2025-09-01 08:48:00+00:00');

INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(4, 'EMAIL_RECEIVED', 'system', 'Email received from alerts@medwatch-systems.com', TIMESTAMP '2025-08-25 11:00:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(4, 'AI_CLASSIFIED', 'ai-service', 'Classified as SAFETY_REPORT (confidence: 0.94)', TIMESTAMP '2025-08-25 11:03:00+00:00');

INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(5, 'EMAIL_RECEIVED', 'system', 'Email received from nora.kapoor@stanford.edu', TIMESTAMP '2025-09-03 15:20:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(5, 'AI_CLASSIFIED', 'ai-service', 'Classified as INFO_REQUEST (confidence: 0.72)', TIMESTAMP '2025-09-03 15:22:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(5, 'REVIEW_OVERRIDDEN', 'admin.chen', 'Overridden from INFO_REQUEST to NOT_RELEVANT', TIMESTAMP '2025-09-03 16:30:00+00:00');

INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(6, 'EMAIL_RECEIVED', 'system', 'Email received from james.omalley@cityhospital.org', TIMESTAMP '2025-08-18 10:45:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(6, 'DOCUMENT_RECEIVED', 'system', 'Document attached: medication-error-report.pdf', TIMESTAMP '2025-08-18 10:46:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(6, 'AI_CLASSIFIED', 'ai-service', 'Classified as QUALITY_COMPLAINT (confidence: 0.85)', TIMESTAMP '2025-08-18 10:48:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(6, 'REVIEW_ACCEPTED', 'dr.smith', 'Accepted classification: QUALITY_COMPLAINT', TIMESTAMP '2025-08-18 12:00:00+00:00');

INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(7, 'EMAIL_RECEIVED', 'system', 'Email received from marketing@healthtech-solutions.com', TIMESTAMP '2025-09-05 09:00:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(7, 'AI_CLASSIFIED', 'ai-service', 'Classified as NOT_RELEVANT (confidence: 0.96)', TIMESTAMP '2025-09-05 09:02:00+00:00');

INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(8, 'EMAIL_RECEIVED', 'system', 'Email received from pharmacovigilance@globalpharma.com', TIMESTAMP '2025-08-28 16:30:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(8, 'DOCUMENT_RECEIVED', 'system', 'Document attached: adverse-event-iccsr.pdf', TIMESTAMP '2025-08-28 16:31:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(8, 'AI_CLASSIFIED', 'ai-service', 'Classified as SAFETY_REPORT (confidence: 0.97)', TIMESTAMP '2025-08-28 16:33:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(8, 'REVIEW_ACCEPTED', 'dr.patel', 'Accepted classification: SAFETY_REPORT', TIMESTAMP '2025-08-28 17:30:00+00:00');

INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(9, 'EMAIL_RECEIVED', 'system', 'Email received from supply.chain@medequip-solutions.com', TIMESTAMP '2025-09-02 13:15:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(9, 'AI_CLASSIFIED', 'ai-service', 'Classified as QUALITY_COMPLAINT (confidence: 0.90)', TIMESTAMP '2025-09-02 13:18:00+00:00');

INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(10, 'EMAIL_RECEIVED', 'system', 'Email received from office.manager@wellness-clinic.com', TIMESTAMP '2025-09-04 11:30:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(10, 'AI_CLASSIFIED', 'ai-service', 'Classified as QUALITY_COMPLAINT/INFO_REQUEST', TIMESTAMP '2025-09-04 11:33:00+00:00');
INSERT INTO audit_logs (email_id, action, actor_id, details, timestamp) VALUES
(10, 'REVIEW_OVERRIDDEN', 'admin.chen', 'Overridden from QUALITY_COMPLAINT to INFO_REQUEST', TIMESTAMP '2025-09-04 13:00:00+00:00');
