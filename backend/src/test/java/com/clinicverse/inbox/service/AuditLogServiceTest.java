package com.clinicverse.inbox.service;

import com.clinicverse.inbox.dto.AuditLogResponse;
import com.clinicverse.inbox.entity.AuditAction;
import com.clinicverse.inbox.entity.AuditLog;
import com.clinicverse.inbox.repository.AuditLogRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuditLogServiceTest {

    @Mock private AuditLogRepository auditLogRepo;

    private AuditLogService auditLogService;

    @BeforeEach
    void setUp() {
        auditLogService = new AuditLogService(auditLogRepo);
    }

    // ========== LIST ALL TESTS ==========

    @Test
    void listAuditLogs_returnsAllLogs() {
        AuditLog log1 = createLog(1L, AuditAction.EMAIL_RECEIVED, "imap", "Email received");
        AuditLog log2 = createLog(2L, AuditAction.AI_CLASSIFIED, "ai-service", "Classified as SAFETY_REPORT");
        when(auditLogRepo.findAllByOrderByTimestampDesc()).thenReturn(List.of(log2, log1));

        List<AuditLogResponse> results = auditLogService.listAuditLogs();

        assertEquals(2, results.size());
        assertEquals(AuditAction.AI_CLASSIFIED, results.get(0).action());
        assertEquals(AuditAction.EMAIL_RECEIVED, results.get(1).action());
    }

    @Test
    void listAuditLogs_returnsEmptyListWhenNone() {
        when(auditLogRepo.findAllByOrderByTimestampDesc()).thenReturn(List.of());

        List<AuditLogResponse> results = auditLogService.listAuditLogs();

        assertTrue(results.isEmpty());
    }

    // ========== BY EMAIL TESTS ==========

    @Test
    void getAuditLogsByEmail_returnsLogsForEmail() {
        AuditLog log1 = createLog(1L, AuditAction.EMAIL_RECEIVED, "imap", "Email received");
        AuditLog log2 = createLog(1L, AuditAction.AI_CLASSIFIED, "ai-service", "Classified");
        when(auditLogRepo.findByEmailIdOrderByTimestampDesc(1L)).thenReturn(List.of(log2, log1));

        List<AuditLogResponse> results = auditLogService.getAuditLogsByEmail(1L);

        assertEquals(2, results.size());
        results.forEach(r -> assertEquals(1L, r.emailId()));
    }

    @Test
    void getAuditLogsByEmail_returnsEmptyForUnknownEmail() {
        when(auditLogRepo.findByEmailIdOrderByTimestampDesc(99L)).thenReturn(List.of());

        List<AuditLogResponse> results = auditLogService.getAuditLogsByEmail(99L);

        assertTrue(results.isEmpty());
    }

    // ========== BY ACTION TESTS ==========

    @Test
    void getAuditLogsByAction_returnsLogsForAction() {
        AuditLog log1 = createLog(1L, AuditAction.AI_CLASSIFIED, "ai-service", "Classified 1");
        AuditLog log2 = createLog(2L, AuditAction.AI_CLASSIFIED, "ai-service", "Classified 2");
        when(auditLogRepo.findByActionOrderByTimestampDesc(AuditAction.AI_CLASSIFIED))
            .thenReturn(List.of(log2, log1));

        List<AuditLogResponse> results = auditLogService.getAuditLogsByAction(AuditAction.AI_CLASSIFIED);

        assertEquals(2, results.size());
        results.forEach(r -> assertEquals(AuditAction.AI_CLASSIFIED, r.action()));
    }

    // ========== BY EMAIL AND ACTION TESTS ==========

    @Test
    void getAuditLogsByEmailAndAction_returnsFilteredLogs() {
        AuditLog log = createLog(1L, AuditAction.REVIEW_ACCEPTED, "reviewer", "Accepted");
        when(auditLogRepo.findByEmailIdAndActionOrderByTimestampDesc(1L, AuditAction.REVIEW_ACCEPTED))
            .thenReturn(List.of(log));

        List<AuditLogResponse> results = auditLogService.getAuditLogsByEmailAndAction(1L, AuditAction.REVIEW_ACCEPTED);

        assertEquals(1, results.size());
        assertEquals(AuditAction.REVIEW_ACCEPTED, results.get(0).action());
        assertEquals(1L, results.get(0).emailId());
    }

    // ========== STATS TESTS ==========

    @Test
    void getAuditStats_returnsCountsByAction() {
        AuditLog log1 = createLog(1L, AuditAction.EMAIL_RECEIVED, "imap", "1");
        AuditLog log2 = createLog(1L, AuditAction.AI_CLASSIFIED, "ai-service", "2");
        AuditLog log3 = createLog(2L, AuditAction.AI_CLASSIFIED, "ai-service", "3");
        when(auditLogRepo.findAll()).thenReturn(List.of(log1, log2, log3));

        var stats = auditLogService.getAuditStats();

        assertEquals(1L, stats.get(AuditAction.EMAIL_RECEIVED));
        assertEquals(2L, stats.get(AuditAction.AI_CLASSIFIED));
    }

    // ========== ALL ACTION TYPES TESTS ==========

    @Test
    void allActionTypes_areDefined() {
        assertNotNull(AuditAction.EMAIL_RECEIVED);
        assertNotNull(AuditAction.DOCUMENT_RECEIVED);
        assertNotNull(AuditAction.PDF_TEXT_EXTRACTED);
        assertNotNull(AuditAction.OCR_COMPLETED);
        assertNotNull(AuditAction.LANGUAGE_DETECTED);
        assertNotNull(AuditAction.AI_CLASSIFIED);
        assertNotNull(AuditAction.FACTS_EXTRACTED);
        assertNotNull(AuditAction.SUMMARY_GENERATED);
        assertNotNull(AuditAction.REVIEW_ACCEPTED);
        assertNotNull(AuditAction.REVIEW_OVERRIDDEN);
        assertNotNull(AuditAction.PROCESSING_FAILED);
    }

    @Test
    void allActionTypes_haveCorrectValues() {
        assertEquals("EMAIL_RECEIVED", AuditAction.EMAIL_RECEIVED);
        assertEquals("DOCUMENT_RECEIVED", AuditAction.DOCUMENT_RECEIVED);
        assertEquals("PDF_TEXT_EXTRACTED", AuditAction.PDF_TEXT_EXTRACTED);
        assertEquals("OCR_COMPLETED", AuditAction.OCR_COMPLETED);
        assertEquals("LANGUAGE_DETECTED", AuditAction.LANGUAGE_DETECTED);
        assertEquals("AI_CLASSIFIED", AuditAction.AI_CLASSIFIED);
        assertEquals("FACTS_EXTRACTED", AuditAction.FACTS_EXTRACTED);
        assertEquals("SUMMARY_GENERATED", AuditAction.SUMMARY_GENERATED);
        assertEquals("REVIEW_ACCEPTED", AuditAction.REVIEW_ACCEPTED);
        assertEquals("REVIEW_OVERRIDDEN", AuditAction.REVIEW_OVERRIDDEN);
        assertEquals("PROCESSING_FAILED", AuditAction.PROCESSING_FAILED);
    }

    // ========== RESPONSE MAPPING TESTS ==========

    @Test
    void auditLogResponse_mapsCorrectly() {
        AuditLog log = createLog(5L, AuditAction.OCR_COMPLETED, "ai-service", "OCR applied to 3 pages");
        log.setTimestamp(Instant.parse("2025-09-04T12:00:00Z"));

        AuditLogResponse response = AuditLogResponse.fromEntity(log);

        assertEquals(5L, response.emailId());
        assertEquals(AuditAction.OCR_COMPLETED, response.action());
        assertEquals("ai-service", response.actorId());
        assertEquals("OCR applied to 3 pages", response.details());
        assertEquals(Instant.parse("2025-09-04T12:00:00Z"), response.timestamp());
        assertEquals("ai-service", response.source());
    }

    @Test
    void auditLogResponse_extractSource_fromActorId() {
        assertEquals("imap", AuditLogResponse.fromEntity(
            createLog(1L, AuditAction.EMAIL_RECEIVED, "imap", "")).source());
        assertEquals("ai-service", AuditLogResponse.fromEntity(
            createLog(1L, AuditAction.AI_CLASSIFIED, "ai-service", "")).source());
        assertEquals("reviewer", AuditLogResponse.fromEntity(
            createLog(1L, AuditAction.REVIEW_ACCEPTED, "reviewer-001", "")).source());
        assertEquals("reviewer", AuditLogResponse.fromEntity(
            createLog(1L, AuditAction.REVIEW_OVERRIDDEN, "admin.chen", "")).source());
        assertEquals("system", AuditLogResponse.fromEntity(
            createLog(1L, AuditAction.PROCESSING_FAILED, "system", "")).source());
        assertEquals("system", AuditLogResponse.fromEntity(
            createLog(1L, AuditAction.EMAIL_RECEIVED, null, "")).source());
    }

    // ========== HELPER METHODS ==========

    private AuditLog createLog(Long emailId, String action, String actorId, String details) {
        AuditLog log = new AuditLog(emailId, action, actorId, details);
        log.setId(1L);
        return log;
    }
}
