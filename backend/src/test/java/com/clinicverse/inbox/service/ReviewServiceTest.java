package com.clinicverse.inbox.service;

import com.clinicverse.inbox.dto.AcceptReviewRequest;
import com.clinicverse.inbox.dto.OverrideReviewRequest;
import com.clinicverse.inbox.dto.ReviewResponse;
import com.clinicverse.inbox.entity.Classification;
import com.clinicverse.inbox.entity.Email;
import com.clinicverse.inbox.entity.Review;
import com.clinicverse.inbox.exception.ResourceNotFoundException;
import com.clinicverse.inbox.repository.AuditLogRepository;
import com.clinicverse.inbox.repository.EmailRepository;
import com.clinicverse.inbox.repository.ReviewRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ReviewServiceTest {

    @Mock private EmailRepository emailRepo;
    @Mock private ReviewRepository reviewRepo;
    @Mock private AuditLogRepository auditLogRepo;

    private ReviewService reviewService;

    private Email testEmail;
    private Classification testClassification;

    @BeforeEach
    void setUp() {
        reviewService = new ReviewService(emailRepo, reviewRepo, auditLogRepo);

        testEmail = new Email("Test Subject", "sender@test.com", "recipient@test.com",
            "Test body", Instant.now());
        testEmail.setId(1L);

        testClassification = new Classification(testEmail, "SAFETY_REPORT", 0.92,
            "[{\"category\":\"SAFETY_REPORT\",\"confidence\":0.92}]");
        testEmail.setClassification(testClassification);
    }

    // ========== ACCEPT REVIEW TESTS ==========

    @Test
    void acceptReview_savesReviewWithCorrectFields() {
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));
        when(reviewRepo.existsByEmailId(1L)).thenReturn(false);
        when(reviewRepo.save(any(Review.class))).thenAnswer(inv -> {
            Review r = inv.getArgument(0);
            r.setId(1L);
            return r;
        });

        AcceptReviewRequest request = new AcceptReviewRequest("dr.smith", "Looks correct");
        Review result = reviewService.acceptReview(1L, request);

        assertEquals("dr.smith", result.getReviewerId());
        assertEquals(Review.ReviewAction.ACCEPTED, result.getAction());
        assertEquals("SAFETY_REPORT", result.getOriginalCategory());
        assertEquals(0.92, result.getOriginalConfidence(), 0.001);
        assertEquals("SAFETY_REPORT", result.getFinalCategory());
        assertNull(result.getOverriddenCategory());
        assertEquals("Looks correct", result.getNotes());
    }

    @Test
    void acceptReview_savesOriginalConfidenceFromClassification() {
        testClassification.setPrimaryConfidence(0.78);
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));
        when(reviewRepo.existsByEmailId(1L)).thenReturn(false);
        when(reviewRepo.save(any(Review.class))).thenAnswer(inv -> {
            Review r = inv.getArgument(0);
            r.setId(1L);
            return r;
        });

        AcceptReviewRequest request = new AcceptReviewRequest("dr.smith", null);
        Review result = reviewService.acceptReview(1L, request);

        assertEquals(0.78, result.getOriginalConfidence(), 0.001);
    }

    @Test
    void acceptReview_createsAuditLog() {
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));
        when(reviewRepo.existsByEmailId(1L)).thenReturn(false);
        when(reviewRepo.save(any(Review.class))).thenAnswer(inv -> {
            Review r = inv.getArgument(0);
            r.setId(1L);
            return r;
        });

        AcceptReviewRequest request = new AcceptReviewRequest("dr.smith", null);
        reviewService.acceptReview(1L, request);

        ArgumentCaptor<com.clinicverse.inbox.entity.AuditLog> captor =
            ArgumentCaptor.forClass(com.clinicverse.inbox.entity.AuditLog.class);
        verify(auditLogRepo).save(captor.capture());

        com.clinicverse.inbox.entity.AuditLog log = captor.getValue();
        assertEquals(1L, log.getEmailId());
        assertEquals("REVIEW_ACCEPTED", log.getAction());
        assertEquals("dr.smith", log.getActorId());
        assertTrue(log.getDetails().contains("SAFETY_REPORT"));
        assertTrue(log.getDetails().contains("92.0%"));
    }

    @Test
    void acceptReview_updatesEmailClassification() {
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));
        when(reviewRepo.existsByEmailId(1L)).thenReturn(false);
        when(reviewRepo.save(any(Review.class))).thenAnswer(inv -> {
            Review r = inv.getArgument(0);
            r.setId(1L);
            return r;
        });

        AcceptReviewRequest request = new AcceptReviewRequest("dr.smith", null);
        reviewService.acceptReview(1L, request);

        // Classification should remain unchanged on accept
        assertEquals("SAFETY_REPORT", testEmail.getClassification().getPrimaryCategory());
    }

    @Test
    void acceptReview_throwsWhenEmailNotFound() {
        when(emailRepo.findById(99L)).thenReturn(Optional.empty());

        AcceptReviewRequest request = new AcceptReviewRequest("dr.smith", null);
        assertThrows(ResourceNotFoundException.class,
            () -> reviewService.acceptReview(99L, request));
    }

    @Test
    void acceptReview_throwsWhenNoClassification() {
        testEmail.setClassification(null);
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));

        AcceptReviewRequest request = new AcceptReviewRequest("dr.smith", null);
        assertThrows(ResourceNotFoundException.class,
            () -> reviewService.acceptReview(1L, request));
    }

    @Test
    void acceptReview_throwsWhenAlreadyReviewed() {
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));
        when(reviewRepo.existsByEmailId(1L)).thenReturn(true);

        AcceptReviewRequest request = new AcceptReviewRequest("dr.smith", null);
        assertThrows(IllegalStateException.class,
            () -> reviewService.acceptReview(1L, request));
    }

    @Test
    void acceptReview_withNullNotes() {
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));
        when(reviewRepo.existsByEmailId(1L)).thenReturn(false);
        when(reviewRepo.save(any(Review.class))).thenAnswer(inv -> {
            Review r = inv.getArgument(0);
            r.setId(1L);
            return r;
        });

        AcceptReviewRequest request = new AcceptReviewRequest("dr.smith", null);
        Review result = reviewService.acceptReview(1L, request);

        assertNull(result.getNotes());
    }

    // ========== OVERRIDE REVIEW TESTS ==========

    @Test
    void overrideReview_savesReviewWithCorrectFields() {
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));
        when(reviewRepo.existsByEmailId(1L)).thenReturn(false);
        when(reviewRepo.save(any(Review.class))).thenAnswer(inv -> {
            Review r = inv.getArgument(0);
            r.setId(1L);
            return r;
        });
        when(emailRepo.save(any(Email.class))).thenAnswer(inv -> inv.getArgument(0));

        OverrideReviewRequest request = new OverrideReviewRequest(
            "admin.chen", "QUALITY_COMPLAINT", "Reclassified per policy");
        Review result = reviewService.overrideReview(1L, request);

        assertEquals("admin.chen", result.getReviewerId());
        assertEquals(Review.ReviewAction.OVERRIDDEN, result.getAction());
        assertEquals("SAFETY_REPORT", result.getOriginalCategory());
        assertEquals(0.92, result.getOriginalConfidence(), 0.001);
        assertEquals("QUALITY_COMPLAINT", result.getOverriddenCategory());
        assertEquals("QUALITY_COMPLAINT", result.getFinalCategory());
        assertEquals("Reclassified per policy", result.getNotes());
    }

    @Test
    void overrideReview_updatesEmailClassification() {
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));
        when(reviewRepo.existsByEmailId(1L)).thenReturn(false);
        when(reviewRepo.save(any(Review.class))).thenAnswer(inv -> {
            Review r = inv.getArgument(0);
            r.setId(1L);
            return r;
        });
        when(emailRepo.save(any(Email.class))).thenAnswer(inv -> inv.getArgument(0));

        OverrideReviewRequest request = new OverrideReviewRequest(
            "admin.chen", "QUALITY_COMPLAINT", null);
        reviewService.overrideReview(1L, request);

        assertEquals("QUALITY_COMPLAINT", testEmail.getClassification().getPrimaryCategory());
    }

    @Test
    void overrideReview_createsAuditLog() {
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));
        when(reviewRepo.existsByEmailId(1L)).thenReturn(false);
        when(reviewRepo.save(any(Review.class))).thenAnswer(inv -> {
            Review r = inv.getArgument(0);
            r.setId(1L);
            return r;
        });
        when(emailRepo.save(any(Email.class))).thenAnswer(inv -> inv.getArgument(0));

        OverrideReviewRequest request = new OverrideReviewRequest(
            "admin.chen", "QUALITY_COMPLAINT", null);
        reviewService.overrideReview(1L, request);

        ArgumentCaptor<com.clinicverse.inbox.entity.AuditLog> captor =
            ArgumentCaptor.forClass(com.clinicverse.inbox.entity.AuditLog.class);
        verify(auditLogRepo).save(captor.capture());

        com.clinicverse.inbox.entity.AuditLog log = captor.getValue();
        assertEquals(1L, log.getEmailId());
        assertEquals("REVIEW_OVERRIDDEN", log.getAction());
        assertEquals("admin.chen", log.getActorId());
        assertTrue(log.getDetails().contains("SAFETY_REPORT"));
        assertTrue(log.getDetails().contains("QUALITY_COMPLAINT"));
    }

    @Test
    void overrideReview_throwsWhenEmailNotFound() {
        when(emailRepo.findById(99L)).thenReturn(Optional.empty());

        OverrideReviewRequest request = new OverrideReviewRequest(
            "admin.chen", "QUALITY_COMPLAINT", null);
        assertThrows(ResourceNotFoundException.class,
            () -> reviewService.overrideReview(99L, request));
    }

    @Test
    void overrideReview_throwsWhenNoClassification() {
        testEmail.setClassification(null);
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));

        OverrideReviewRequest request = new OverrideReviewRequest(
            "admin.chen", "QUALITY_COMPLAINT", null);
        assertThrows(ResourceNotFoundException.class,
            () -> reviewService.overrideReview(1L, request));
    }

    @Test
    void overrideReview_throwsWhenAlreadyReviewed() {
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));
        when(reviewRepo.existsByEmailId(1L)).thenReturn(true);

        OverrideReviewRequest request = new OverrideReviewRequest(
            "admin.chen", "QUALITY_COMPLAINT", null);
        assertThrows(IllegalStateException.class,
            () -> reviewService.overrideReview(1L, request));
    }

    @Test
    void overrideReview_savesOriginalCategoryBeforeUpdate() {
        when(emailRepo.findById(1L)).thenReturn(Optional.of(testEmail));
        when(reviewRepo.existsByEmailId(1L)).thenReturn(false);
        when(reviewRepo.save(any(Review.class))).thenAnswer(inv -> {
            Review r = inv.getArgument(0);
            r.setId(1L);
            return r;
        });
        when(emailRepo.save(any(Email.class))).thenAnswer(inv -> inv.getArgument(0));

        OverrideReviewRequest request = new OverrideReviewRequest(
            "admin.chen", "NOT_RELEVANT", null);
        Review result = reviewService.overrideReview(1L, request);

        // Original should still be SAFETY_REPORT
        assertEquals("SAFETY_REPORT", result.getOriginalCategory());
        // Final should be NOT_RELEVANT
        assertEquals("NOT_RELEVANT", result.getFinalCategory());
    }

    @Test
    void overrideReview_allFourValidCategories() {
        String[] categories = {"SAFETY_REPORT", "QUALITY_COMPLAINT", "INFO_REQUEST", "NOT_RELEVANT"};

        for (String cat : categories) {
            Email email = new Email("Test", "a@b.com", "c@d.com", "body", Instant.now());
            email.setId(10L);
            Classification cls = new Classification(email, "SAFETY_REPORT", 0.9, "[]");
            email.setClassification(cls);

            when(emailRepo.findById(10L)).thenReturn(Optional.of(email));
            when(reviewRepo.existsByEmailId(10L)).thenReturn(false);
            when(reviewRepo.save(any(Review.class))).thenAnswer(inv -> {
                Review r = inv.getArgument(0);
                r.setId(20L);
                return r;
            });
            when(emailRepo.save(any(Email.class))).thenAnswer(inv -> inv.getArgument(0));

            OverrideReviewRequest request = new OverrideReviewRequest("reviewer", cat, null);
            Review result = reviewService.overrideReview(10L, request);

            assertEquals(cat, result.getOverriddenCategory());
            assertEquals(cat, result.getFinalCategory());
            assertEquals("SAFETY_REPORT", result.getOriginalCategory());
        }
    }

    // ========== GET REVIEW TESTS ==========

    @Test
    void getReview_returnsReviewForEmail() {
        Review review = new Review(testEmail, "dr.smith", Review.ReviewAction.ACCEPTED);
        review.setOriginalCategory("SAFETY_REPORT");
        review.setOriginalConfidence(0.92);
        review.setFinalCategory("SAFETY_REPORT");
        review.setId(1L);

        when(reviewRepo.findByEmailId(1L)).thenReturn(Optional.of(review));

        ReviewResponse response = reviewService.getReview(1L);

        assertEquals(1L, response.id());
        assertEquals("SAFETY_REPORT", response.originalCategory());
        assertEquals("ACCEPTED", response.action());
    }

    @Test
    void getReview_throwsWhenNotFound() {
        when(reviewRepo.findByEmailId(99L)).thenReturn(Optional.empty());

        assertThrows(ResourceNotFoundException.class,
            () -> reviewService.getReview(99L));
    }

    // ========== LIST ALL REVIEWS TESTS ==========

    @Test
    void listAllReviews_returnsAllReviews() {
        Review r1 = new Review(testEmail, "dr.smith", Review.ReviewAction.ACCEPTED);
        r1.setOriginalCategory("SAFETY_REPORT");
        r1.setFinalCategory("SAFETY_REPORT");
        r1.setId(1L);

        Review r2 = new Review(testEmail, "admin.chen", Review.ReviewAction.OVERRIDDEN);
        r2.setOriginalCategory("INFO_REQUEST");
        r2.setOverriddenCategory("NOT_RELEVANT");
        r2.setFinalCategory("NOT_RELEVANT");
        r2.setId(2L);

        when(reviewRepo.findAllByOrderByReviewedAtDesc()).thenReturn(List.of(r2, r1));

        List<ReviewResponse> results = reviewService.listAllReviews();

        assertEquals(2, results.size());
        assertEquals("OVERRIDDEN", results.get(0).action());
        assertEquals("ACCEPTED", results.get(1).action());
    }
}
