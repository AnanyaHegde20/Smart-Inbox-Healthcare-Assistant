package com.clinicverse.inbox.dto;

import com.clinicverse.inbox.entity.Review;
import java.time.Instant;

public record ReviewResponse(
    Long id,
    Long emailId,
    String reviewerId,
    String action,
    String originalCategory,
    Double originalConfidence,
    String overriddenCategory,
    String finalCategory,
    String notes,
    Instant reviewedAt
) {
    public static ReviewResponse fromEntity(Review r) {
        return new ReviewResponse(
            r.getId(),
            r.getEmail() != null ? r.getEmail().getId() : null,
            r.getReviewerId(),
            r.getAction().name(),
            r.getOriginalCategory(),
            r.getOriginalConfidence(),
            r.getOverriddenCategory(),
            r.getFinalCategory(),
            r.getNotes(),
            r.getReviewedAt()
        );
    }
}
