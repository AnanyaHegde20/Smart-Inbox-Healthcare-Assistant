package com.clinicverse.inbox.service;

import com.clinicverse.inbox.dto.AcceptReviewRequest;
import com.clinicverse.inbox.dto.OverrideReviewRequest;
import com.clinicverse.inbox.dto.ReviewResponse;
import com.clinicverse.inbox.entity.Email;
import com.clinicverse.inbox.entity.Review;
import com.clinicverse.inbox.exception.ResourceNotFoundException;
import com.clinicverse.inbox.repository.AuditLogRepository;
import com.clinicverse.inbox.repository.EmailRepository;
import com.clinicverse.inbox.repository.ReviewRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.clinicverse.inbox.entity.AuditLog;

import java.util.List;

@Service
public class ReviewService {

    private static final Logger log = LoggerFactory.getLogger(ReviewService.class);

    private final EmailRepository emailRepo;
    private final ReviewRepository reviewRepo;
    private final AuditLogRepository auditLogRepo;

    public ReviewService(EmailRepository emailRepo, ReviewRepository reviewRepo,
                         AuditLogRepository auditLogRepo) {
        this.emailRepo = emailRepo;
        this.reviewRepo = reviewRepo;
        this.auditLogRepo = auditLogRepo;
    }

    @Transactional
    public Review acceptReview(Long emailId, AcceptReviewRequest request) {
        Email email = findEmail(emailId);

        if (email.getClassification() == null) {
            throw new ResourceNotFoundException("Classification for email", emailId);
        }

        if (reviewRepo.existsByEmailId(emailId)) {
            throw new IllegalStateException("Review already exists for email " + emailId);
        }

        String originalCategory = email.getClassification().getPrimaryCategory();
        Double originalConfidence = email.getClassification().getPrimaryConfidence();

        Review review = new Review(email, request.reviewerId(), Review.ReviewAction.ACCEPTED);
        review.setOriginalCategory(originalCategory);
        review.setOriginalConfidence(originalConfidence);
        review.setFinalCategory(originalCategory);
        review.setNotes(request.notes());
        review = reviewRepo.save(review);

        auditLogRepo.save(new AuditLog(emailId, "REVIEW_ACCEPTED", request.reviewerId(),
            "Accepted classification: " + originalCategory
                + " (confidence: " + String.format("%.1f%%", originalConfidence * 100) + ")"));

        log.info("Review accepted for email {} by {}: {}", emailId, request.reviewerId(), originalCategory);
        return review;
    }

    @Transactional
    public Review overrideReview(Long emailId, OverrideReviewRequest request) {
        Email email = findEmail(emailId);

        if (email.getClassification() == null) {
            throw new ResourceNotFoundException("Classification for email", emailId);
        }

        if (reviewRepo.existsByEmailId(emailId)) {
            throw new IllegalStateException("Review already exists for email " + emailId);
        }

        String originalCategory = email.getClassification().getPrimaryCategory();
        Double originalConfidence = email.getClassification().getPrimaryConfidence();

        Review review = new Review(email, request.reviewerId(), Review.ReviewAction.OVERRIDDEN);
        review.setOriginalCategory(originalCategory);
        review.setOriginalConfidence(originalConfidence);
        review.setOverriddenCategory(request.overriddenCategory());
        review.setFinalCategory(request.overriddenCategory());
        review.setNotes(request.notes());
        review = reviewRepo.save(review);

        email.getClassification().setPrimaryCategory(request.overriddenCategory());
        emailRepo.save(email);

        auditLogRepo.save(new AuditLog(emailId, "REVIEW_OVERRIDDEN", request.reviewerId(),
            "Overridden from " + originalCategory + " (confidence: "
                + String.format("%.1f%%", originalConfidence * 100) + ")"
                + " to " + request.overriddenCategory()));

        log.info("Review overridden for email {} by {}: {} -> {}", emailId, request.reviewerId(),
            originalCategory, request.overriddenCategory());
        return review;
    }

    @Transactional(readOnly = true)
    public ReviewResponse getReview(Long emailId) {
        Review review = reviewRepo.findByEmailId(emailId)
            .orElseThrow(() -> new ResourceNotFoundException("Review for email", emailId));
        return ReviewResponse.fromEntity(review);
    }

    @Transactional(readOnly = true)
    public List<ReviewResponse> listAllReviews() {
        return reviewRepo.findAllByOrderByReviewedAtDesc().stream()
            .map(ReviewResponse::fromEntity)
            .toList();
    }

    @Transactional(readOnly = true)
    public List<ReviewResponse> getReviewsByReviewer(String reviewerId) {
        return reviewRepo.findByReviewerIdOrderByReviewedAtDesc(reviewerId).stream()
            .map(ReviewResponse::fromEntity)
            .toList();
    }

    private Email findEmail(Long id) {
        return emailRepo.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Email", id));
    }
}
