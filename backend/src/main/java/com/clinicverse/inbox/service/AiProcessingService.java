package com.clinicverse.inbox.service;

import com.clinicverse.inbox.entity.*;
import com.clinicverse.inbox.exception.ProcessingException;
import com.clinicverse.inbox.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientException;

import java.util.Map;

@Service
public class AiProcessingService {

    private static final Logger log = LoggerFactory.getLogger(AiProcessingService.class);

    private final WebClient webClient;
    private final EmailRepository emailRepo;
    private final DocumentRepository documentRepo;
    private final ClassificationRepository classificationRepo;
    private final ExtractionRepository extractionRepo;
    private final AuditLogRepository auditLogRepo;

    public AiProcessingService(
            WebClient.Builder webClientBuilder,
            EmailRepository emailRepo,
            DocumentRepository documentRepo,
            ClassificationRepository classificationRepo,
            ExtractionRepository extractionRepo,
            AuditLogRepository auditLogRepo,
            @Value("${ai-service.base-url}") String aiBaseUrl) {
        this.webClient = webClientBuilder.baseUrl(aiBaseUrl).build();
        this.emailRepo = emailRepo;
        this.documentRepo = documentRepo;
        this.classificationRepo = classificationRepo;
        this.extractionRepo = extractionRepo;
        this.auditLogRepo = auditLogRepo;
    }

    @Async
    @Transactional
    public void processEmailAsync(Long emailId) {
        Email email = emailRepo.findById(emailId).orElse(null);
        if (email == null) {
            log.error("Email not found for async processing: {}", emailId);
            return;
        }

        email.setStatus(Email.ProcessingStatus.PROCESSING);
        emailRepo.save(email);

        try {
            Map<String, Object> requestBody = Map.of(
                "filename", email.getSubject() + ".txt",
                "document", email.getBody() != null ? email.getBody() : email.getSubject(),
                "email_metadata", Map.of(
                    "from", email.getSender(),
                    "to", email.getRecipient(),
                    "subject", email.getSubject(),
                    "date", email.getReceivedAt().toString()
                )
            );

            @SuppressWarnings("unchecked")
            Map<String, Object> aiResponse = webClient.post()
                .uri("/api/v1/process-document")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(Map.class)
                .block();

            if (aiResponse == null) {
                throw new ProcessingException("Empty response from AI service");
            }

            // Document processing
            saveDocument(email, aiResponse);
            auditLogRepo.save(new AuditLog(emailId, AuditAction.PDF_TEXT_EXTRACTED, "ai-service",
                "Text extracted from document: " + email.getSubject() + ".txt"));

            // OCR status
            Boolean ocrUsed = Boolean.TRUE.equals(aiResponse.get("ocr_used"));
            if (ocrUsed) {
                auditLogRepo.save(new AuditLog(emailId, AuditAction.OCR_COMPLETED, "ai-service",
                    "OCR processing applied to scanned document"));
            }

            // Language detection
            String language = (String) aiResponse.getOrDefault("language", "en");
            auditLogRepo.save(new AuditLog(emailId, AuditAction.LANGUAGE_DETECTED, "ai-service",
                "Detected language: " + language));

            // Classification
            saveClassification(email, aiResponse);
            Map<String, Object> classOutput = (Map<String, Object>) aiResponse.get("classification_output");
            if (classOutput != null) {
                var categories = (java.util.List<Map<String, Object>>) classOutput.get("categories");
                if (categories != null && !categories.isEmpty()) {
                    String primaryCategory = (String) categories.get(0).get("category");
                    Double confidence = categories.get(0).get("confidence") != null
                        ? ((Number) categories.get(0).get("confidence")).doubleValue() : 0.0;
                    auditLogRepo.save(new AuditLog(emailId, AuditAction.AI_CLASSIFIED, "ai-service",
                        "Primary category: " + primaryCategory
                            + " (confidence: " + String.format("%.1f%%", confidence * 100) + ")"));
                }
            }

            // Fact extraction
            saveExtraction(email, aiResponse);
            String extractionType = detectExtractionType(aiResponse);
            if (extractionType != null) {
                auditLogRepo.save(new AuditLog(emailId, AuditAction.FACTS_EXTRACTED, "ai-service",
                    "Extracted structured facts: " + extractionType));
            }

            // Summary
            String summary = (String) aiResponse.get("summary");
            if (summary != null && !summary.isBlank()) {
                auditLogRepo.save(new AuditLog(emailId, AuditAction.SUMMARY_GENERATED, "ai-service",
                    "Summary generated (" + summary.length() + " chars)"));
            }

            email.setStatus(Email.ProcessingStatus.COMPLETED);
            emailRepo.save(email);

            log.info("AI processing completed for email: {}", emailId);

        } catch (WebClientException ex) {
            log.error("AI service call failed for email {}: {}", emailId, ex.getMessage());
            email.setStatus(Email.ProcessingStatus.FAILED);
            email.setErrorMessage("AI service error: " + ex.getMessage());
            emailRepo.save(email);
            auditLogRepo.save(new AuditLog(emailId, AuditAction.PROCESSING_FAILED, "ai-service",
                "AI service error: " + ex.getMessage()));

        } catch (Exception ex) {
            log.error("Unexpected error processing email {}: {}", emailId, ex.getMessage());
            email.setStatus(Email.ProcessingStatus.FAILED);
            email.setErrorMessage("Processing error: " + ex.getMessage());
            emailRepo.save(email);
            auditLogRepo.save(new AuditLog(emailId, AuditAction.PROCESSING_FAILED, "system",
                "Error: " + ex.getMessage()));
        }
    }

    private void saveDocument(Email email, Map<String, Object> aiResponse) {
        Document doc = new Document(email, email.getSubject() + ".txt", "text/plain", 0L);
        doc.setExtractedText((String) aiResponse.getOrDefault("extracted_text", ""));
        doc.setOcrUsed(Boolean.TRUE.equals(aiResponse.get("ocr_used")));
        doc.setLanguage((String) aiResponse.getOrDefault("language", "en"));
        if (aiResponse.get("total_pages") != null) {
            doc.setPageCount(((Number) aiResponse.get("total_pages")).intValue());
        }
        documentRepo.save(doc);
    }

    @SuppressWarnings("unchecked")
    private void saveClassification(Email email, Map<String, Object> aiResponse) {
        Map<String, Object> classOutput = (Map<String, Object>) aiResponse.get("classification_output");
        if (classOutput == null) return;

        var categories = (java.util.List<Map<String, Object>>) classOutput.get("categories");
        if (categories == null || categories.isEmpty()) return;

        String primaryCategory = (String) categories.get(0).get("category");
        Double primaryConfidence = categories.get(0).get("confidence") != null
            ? ((Number) categories.get(0).get("confidence")).doubleValue() : 0.0;

        Classification classification = new Classification(email, primaryCategory, primaryConfidence,
            categories.toString());
        classification.setSummary((String) aiResponse.get("summary"));

        Map<String, Object> summaryOutput = (Map<String, Object>) aiResponse.get("document_summary");
        if (summaryOutput != null) {
            classification.setIsRelevant((Boolean) summaryOutput.get("is_relevant"));
            classification.setRelevanceConfidence(summaryOutput.get("relevance_confidence") != null
                ? ((Number) summaryOutput.get("relevance_confidence")).doubleValue() : null);
        }

        classificationRepo.save(classification);
    }

    @SuppressWarnings("unchecked")
    private void saveExtraction(Email email, Map<String, Object> aiResponse) {
        Map<String, Object> icsr = (Map<String, Object>) aiResponse.get("icsr_report");
        if (icsr != null) {
            Extraction extraction = new Extraction(email, icsr.toString(), "ICSR", 0.8);
            extractionRepo.save(extraction);
            return;
        }

        Map<String, Object> quality = (Map<String, Object>) aiResponse.get("quality_complaint");
        if (quality != null) {
            Extraction extraction = new Extraction(email, quality.toString(), "QUALITY_COMPLAINT", 0.8);
            extractionRepo.save(extraction);
            return;
        }

        Map<String, Object> infoRequest = (Map<String, Object>) aiResponse.get("info_request");
        if (infoRequest != null) {
            Extraction extraction = new Extraction(email, infoRequest.toString(), "INFO_REQUEST", 0.8);
            extractionRepo.save(extraction);
            return;
        }

        Map<String, Object> notRelevant = (Map<String, Object>) aiResponse.get("not_relevant");
        if (notRelevant != null) {
            Extraction extraction = new Extraction(email, notRelevant.toString(), "NOT_RELEVANT", 0.8);
            extractionRepo.save(extraction);
        }
    }

    private String detectExtractionType(Map<String, Object> aiResponse) {
        if (aiResponse.containsKey("icsr_report")) return "ICSR";
        if (aiResponse.containsKey("quality_complaint")) return "QUALITY_COMPLAINT";
        if (aiResponse.containsKey("info_request")) return "INFO_REQUEST";
        if (aiResponse.containsKey("not_relevant")) return "NOT_RELEVANT";
        return null;
    }
}
