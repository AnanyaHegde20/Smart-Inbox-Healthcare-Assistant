package com.clinicverse.inbox.entity;

public final class AuditAction {

    private AuditAction() {}

    public static final String EMAIL_RECEIVED = "EMAIL_RECEIVED";
    public static final String DOCUMENT_RECEIVED = "DOCUMENT_RECEIVED";
    public static final String PDF_TEXT_EXTRACTED = "PDF_TEXT_EXTRACTED";
    public static final String OCR_COMPLETED = "OCR_COMPLETED";
    public static final String LANGUAGE_DETECTED = "LANGUAGE_DETECTED";
    public static final String AI_CLASSIFIED = "AI_CLASSIFIED";
    public static final String FACTS_EXTRACTED = "FACTS_EXTRACTED";
    public static final String SUMMARY_GENERATED = "SUMMARY_GENERATED";
    public static final String REVIEW_ACCEPTED = "REVIEW_ACCEPTED";
    public static final String REVIEW_OVERRIDDEN = "REVIEW_OVERRIDDEN";
    public static final String PROCESSING_FAILED = "PROCESSING_FAILED";
}
