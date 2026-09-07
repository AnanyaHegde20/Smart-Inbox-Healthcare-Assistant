package com.clinicverse.inbox.controller;

import com.clinicverse.inbox.dto.AcceptReviewRequest;
import com.clinicverse.inbox.dto.OverrideReviewRequest;
import com.clinicverse.inbox.entity.Review;
import com.clinicverse.inbox.repository.AuditLogRepository;
import com.clinicverse.inbox.repository.ReviewRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ApiIntegrationTest {

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;
    @Autowired private ReviewRepository reviewRepository;
    @Autowired private AuditLogRepository auditLogRepository;

    // ================================================================
    // 1. GET /api/emails — returns seeded emails
    // ================================================================

    @Test
    void listEmails_returnsSeededEmails() throws Exception {
        mockMvc.perform(get("/api/emails"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(10))))
                .andExpect(jsonPath("$[0].id").isNumber())
                .andExpect(jsonPath("$[0].subject").isString())
                .andExpect(jsonPath("$[0].sender").isString())
                .andExpect(jsonPath("$[0].status").isString());
    }

    // ================================================================
    // 2. GET /api/emails/{id} — returns an existing email
    // ================================================================

    @Test
    void getEmail_returnsExistingEmail() throws Exception {
        mockMvc.perform(get("/api/emails/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.subject", containsString("Patient Fall")))
                .andExpect(jsonPath("$.sender").value("dr.elena.vasquez@meridian-general.org"))
                .andExpect(jsonPath("$.status").value("COMPLETED"));
    }

    // ================================================================
    // 3. GET /api/emails/{id}/documents — returns documents
    // ================================================================

    @Test
    void getDocuments_returnsDocumentsForEmail() throws Exception {
        mockMvc.perform(get("/api/emails/1/documents"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(1))))
                .andExpect(jsonPath("$[0].emailId").value(1))
                .andExpect(jsonPath("$[0].filename").isString())
                .andExpect(jsonPath("$[0].contentType").isString());
    }

    @Test
    void getDocuments_returnsEmptyForEmailWithNoDocs() throws Exception {
        // Email 999 doesn't exist — should 404
        mockMvc.perform(get("/api/emails/999/documents"))
                .andExpect(status().isNotFound());
    }

    // ================================================================
    // 4. GET /api/emails/{id}/classification — returns classification
    // ================================================================

    @Test
    void getClassification_returnsClassificationForEmail() throws Exception {
        mockMvc.perform(get("/api/emails/1/classification"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.emailId").value(1))
                .andExpect(jsonPath("$.primaryCategory").value("SAFETY_REPORT"))
                .andExpect(jsonPath("$.primaryConfidence").value(0.95))
                .andExpect(jsonPath("$.isRelevant").value(true));
    }

    @Test
    void getClassification_returnsClassificationForQualityEmail() throws Exception {
        mockMvc.perform(get("/api/emails/2/classification"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.primaryCategory").value("QUALITY_COMPLAINT"))
                .andExpect(jsonPath("$.primaryConfidence").value(0.92));
    }

    // ================================================================
    // 5. GET /api/emails/{id}/extraction — returns extracted fields
    // ================================================================

    @Test
    void getExtraction_returnsExtractionForEmail() throws Exception {
        mockMvc.perform(get("/api/emails/1/extraction"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.emailId").value(1))
                .andExpect(jsonPath("$.extractedData").isString())
                .andExpect(jsonPath("$.extractionType").value("ICSR"))
                .andExpect(jsonPath("$.confidenceScore").value(0.90));
    }

    @Test
    void getExtraction_returnsExtractionForQualityEmail() throws Exception {
        mockMvc.perform(get("/api/emails/2/extraction"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.extractionType").value("QUALITY_COMPLAINT"));
    }

    // ================================================================
    // 6. GET /api/reviews — returns reviews
    // ================================================================

    @Test
    void listReviews_returnsSeededReviews() throws Exception {
        mockMvc.perform(get("/api/reviews"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(5))))
                .andExpect(jsonPath("$[0].id").isNumber())
                .andExpect(jsonPath("$[0].reviewerId").isString())
                .andExpect(jsonPath("$[0].action").isString())
                .andExpect(jsonPath("$[0].finalCategory").isString());
    }

    @Test
    void listReviews_containsAcceptedAndOverridden() throws Exception {
        mockMvc.perform(get("/api/reviews"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[?(@.action == 'ACCEPTED')]", hasSize(greaterThanOrEqualTo(3))))
                .andExpect(jsonPath("$[?(@.action == 'OVERRIDDEN')]", hasSize(greaterThanOrEqualTo(2))));
    }

    // ================================================================
    // 7. POST /api/reviews/{id}/accept — accepts a review
    // ================================================================

    @Test
    void acceptReview_savesReviewAndAuditLog() throws Exception {
        // Email 2 has no review yet
        long emailId = 2;
        long auditCountBefore = auditLogRepository.count();

        AcceptReviewRequest request = new AcceptReviewRequest("dr.test", "Integration test accept");
        mockMvc.perform(post("/api/reviews/" + emailId + "/accept")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.action").value("ACCEPTED"))
                .andExpect(jsonPath("$.finalCategory").value("QUALITY_COMPLAINT"))
                .andExpect(jsonPath("$.message").value("Classification accepted"));

        // Verify review persisted
        assertTrue(reviewRepository.existsByEmailId(emailId));
        Review review = reviewRepository.findByEmailId(emailId).orElseThrow();
        assertEquals("dr.test", review.getReviewerId());
        assertEquals(Review.ReviewAction.ACCEPTED, review.getAction());
        assertEquals("QUALITY_COMPLAINT", review.getOriginalCategory());
        assertEquals("QUALITY_COMPLAINT", review.getFinalCategory());

        // Verify audit log created
        long auditCountAfter = auditLogRepository.count();
        assertTrue(auditCountAfter > auditCountBefore,
                "Audit log count should increase after accept");

        var auditLogs = auditLogRepository.findByEmailIdAndActionOrderByTimestampDesc(
                emailId, "REVIEW_ACCEPTED");
        assertFalse(auditLogs.isEmpty(), "REVIEW_ACCEPTED audit log should exist");
        assertEquals("dr.test", auditLogs.get(0).getActorId());
    }

    // ================================================================
    // 8. POST /api/reviews/{id}/override — overrides a review
    // ================================================================

    @Test
    void overrideReview_changesCategoryAndCreatesAuditLog() throws Exception {
        // Email 3 has no review yet, classification is INFO_REQUEST
        long emailId = 3;
        long auditCountBefore = auditLogRepository.count();

        OverrideReviewRequest request = new OverrideReviewRequest(
                "admin.test", "NOT_RELEVANT", "Reclassified for testing");
        mockMvc.perform(post("/api/reviews/" + emailId + "/override")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.action").value("OVERRIDDEN"))
                .andExpect(jsonPath("$.overriddenCategory").value("NOT_RELEVANT"))
                .andExpect(jsonPath("$.finalCategory").value("NOT_RELEVANT"))
                .andExpect(jsonPath("$.message").value("Classification overridden"));

        // Verify review persisted
        assertTrue(reviewRepository.existsByEmailId(emailId));
        Review review = reviewRepository.findByEmailId(emailId).orElseThrow();
        assertEquals("admin.test", review.getReviewerId());
        assertEquals(Review.ReviewAction.OVERRIDDEN, review.getAction());
        assertEquals("INFO_REQUEST", review.getOriginalCategory());
        assertEquals("NOT_RELEVANT", review.getOverriddenCategory());
        assertEquals("NOT_RELEVANT", review.getFinalCategory());

        // Verify audit log created
        long auditCountAfter = auditLogRepository.count();
        assertTrue(auditCountAfter > auditCountBefore,
                "Audit log count should increase after override");

        var auditLogs = auditLogRepository.findByEmailIdAndActionOrderByTimestampDesc(
                emailId, "REVIEW_OVERRIDDEN");
        assertFalse(auditLogs.isEmpty(), "REVIEW_OVERRIDDEN audit log should exist");
        assertEquals("admin.test", auditLogs.get(0).getActorId());
    }

    // ================================================================
    // 9. GET /api/audit-logs — returns audit events
    // ================================================================

    @Test
    void listAuditLogs_returnsSeededAuditLogs() throws Exception {
        mockMvc.perform(get("/api/audit-logs"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(30))))
                .andExpect(jsonPath("$[0].id").isNumber())
                .andExpect(jsonPath("$[0].emailId").isNumber())
                .andExpect(jsonPath("$[0].action").isString())
                .andExpect(jsonPath("$[0].details").isString())
                .andExpect(jsonPath("$[0].timestamp").isString());
    }

    @Test
    void listAuditLogs_byEmail() throws Exception {
        mockMvc.perform(get("/api/audit-logs/email/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(5))))
                .andExpect(jsonPath("$[?(@.emailId == 1)]", hasSize(greaterThanOrEqualTo(5))));
    }

    @Test
    void listAuditLogs_byAction() throws Exception {
        mockMvc.perform(get("/api/audit-logs/action/AI_CLASSIFIED"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(8))))
                .andExpect(jsonPath("$[?(@.action == 'AI_CLASSIFIED')]",
                        hasSize(greaterThanOrEqualTo(8))));
    }

    // ================================================================
    // 10. GET /api/audit-logs/stats — returns statistics
    // ================================================================

    @Test
    void getAuditStats_returnsActionCounts() throws Exception {
        mockMvc.perform(get("/api/audit-logs/stats"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.EMAIL_RECEIVED").value(greaterThanOrEqualTo(10)))
                .andExpect(jsonPath("$.AI_CLASSIFIED").value(greaterThanOrEqualTo(8)));
    }

    // ================================================================
    // 11. Invalid/nonexistent email ID — returns 404
    // ================================================================

    @Test
    void getEmail_nonexistent_returns404() throws Exception {
        mockMvc.perform(get("/api/emails/99999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.error", containsString("not found")));
    }

    @Test
    void getClassification_nonexistentEmail_returns404() throws Exception {
        mockMvc.perform(get("/api/emails/99999/classification"))
                .andExpect(status().isNotFound());
    }

    @Test
    void getExtraction_nonexistentEmail_returns404() throws Exception {
        mockMvc.perform(get("/api/emails/99999/extraction"))
                .andExpect(status().isNotFound());
    }

    @Test
    void getReview_nonexistentEmail_returns404() throws Exception {
        mockMvc.perform(get("/api/reviews/email/99999"))
                .andExpect(status().isNotFound());
    }

    // ================================================================
    // 12. Review validation/error handling
    // ================================================================

    @Test
    void acceptReview_alreadyReviewed_returnsError() throws Exception {
        // Email 1 already has a review from seed data
        AcceptReviewRequest request = new AcceptReviewRequest("dr.dup", "Duplicate review");
        mockMvc.perform(post("/api/reviews/1/accept")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isInternalServerError());
    }

    @Test
    void overrideReview_alreadyReviewed_returnsError() throws Exception {
        // Email 1 already has a review from seed data
        OverrideReviewRequest request = new OverrideReviewRequest(
                "admin.dup", "QUALITY_COMPLAINT", null);
        mockMvc.perform(post("/api/reviews/1/override")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isInternalServerError());
    }

    @Test
    void acceptReview_missingReviewerId_returns400() throws Exception {
        String body = "{\"notes\":\"no reviewer id\"}";
        mockMvc.perform(post("/api/reviews/2/accept")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isBadRequest());
    }

    @Test
    void overrideReview_missingRequiredFields_returns400() throws Exception {
        String body = "{\"reviewerId\":\"admin.test\"}";
        mockMvc.perform(post("/api/reviews/3/override")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isBadRequest());
    }

    @Test
    void acceptReview_nonexistentEmail_returns404() throws Exception {
        AcceptReviewRequest request = new AcceptReviewRequest("dr.test", null);
        mockMvc.perform(post("/api/reviews/99999/accept")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isNotFound());
    }

    @Test
    void overrideReview_nonexistentEmail_returns404() throws Exception {
        OverrideReviewRequest request = new OverrideReviewRequest(
                "admin.test", "NOT_RELEVANT", null);
        mockMvc.perform(post("/api/reviews/99999/override")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isNotFound());
    }

    @Test
    void acceptReview_unreviewedEmailWithClassification_succeeds() throws Exception {
        // Email 7 has classification (NOT_RELEVANT) and no review in seed data
        AcceptReviewRequest request = new AcceptReviewRequest("dr.test", "Edge case test");
        mockMvc.perform(post("/api/reviews/7/accept")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.action").value("ACCEPTED"))
                .andExpect(jsonPath("$.finalCategory").value("NOT_RELEVANT"));
    }

    // ================================================================
    // 13. Database persistence verification
    // ================================================================

    @Test
    void acceptReview_persistsReviewToDatabase() throws Exception {
        // Email 7 was used in acceptReview_unreviewedEmailWithClassification_succeeds
        // Use email 4 which has no review in seed data
        long emailId = 4;
        AcceptReviewRequest request = new AcceptReviewRequest("dr.persistence", "Verify DB write");
        mockMvc.perform(post("/api/reviews/" + emailId + "/accept")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk());

        // Direct DB verification
        Review review = reviewRepository.findByEmailId(emailId).orElseThrow();
        assertNotNull(review.getId(), "Review should have a generated ID");
        assertEquals("dr.persistence", review.getReviewerId());
        assertEquals(Review.ReviewAction.ACCEPTED, review.getAction());
        assertNotNull(review.getReviewedAt(), "Reviewed timestamp should be set");
    }

    @Test
    void overrideReview_persistsReviewAndUpdatesClassification() throws Exception {
        long emailId = 9;
        OverrideReviewRequest request = new OverrideReviewRequest(
                "admin.persistence", "INFO_REQUEST", "DB persistence test");
        mockMvc.perform(post("/api/reviews/" + emailId + "/override")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk());

        // Verify review in DB
        Review review = reviewRepository.findByEmailId(emailId).orElseThrow();
        assertNotNull(review.getId());
        assertEquals("admin.persistence", review.getReviewerId());
        assertEquals("QUALITY_COMPLAINT", review.getOriginalCategory());
        assertEquals("INFO_REQUEST", review.getOverriddenCategory());
        assertEquals("INFO_REQUEST", review.getFinalCategory());

        // Verify classification was updated in DB
        mockMvc.perform(get("/api/emails/" + emailId + "/classification"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.primaryCategory").value("INFO_REQUEST"));
    }

    @Test
    void auditLog_persistsWithCorrectTimestamp() throws Exception {
        // Verify that the audit logs from the override test (email 9) have valid timestamps
        // The overrideReview_persistsReviewAndUpdatesClassification test already created
        // a REVIEW_OVERRIDDEN audit log for email 9
        var logs = auditLogRepository.findByEmailIdOrderByTimestampDesc(9L);
        assertFalse(logs.isEmpty(), "Audit logs should exist for email 9");

        // Find the REVIEW_OVERRIDDEN log
        var overrideLogs = logs.stream()
                .filter(l -> "REVIEW_OVERRIDDEN".equals(l.getAction()))
                .toList();
        assertFalse(overrideLogs.isEmpty(), "REVIEW_OVERRIDDEN audit log should exist");
        assertNotNull(overrideLogs.get(0).getTimestamp(), "Audit log timestamp should not be null");
        assertEquals("admin.persistence", overrideLogs.get(0).getActorId());
    }
}
