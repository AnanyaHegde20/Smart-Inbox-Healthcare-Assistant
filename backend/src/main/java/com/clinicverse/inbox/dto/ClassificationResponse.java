package com.clinicverse.inbox.dto;

import com.clinicverse.inbox.entity.Classification;
import java.time.Instant;

public record ClassificationResponse(
    Long id,
    Long emailId,
    String primaryCategory,
    Double primaryConfidence,
    String allCategories,
    String summary,
    Boolean isRelevant,
    Double relevanceConfidence,
    Instant createdAt
) {
    public static ClassificationResponse fromEntity(Classification c) {
        return new ClassificationResponse(
            c.getId(), c.getEmail().getId(), c.getPrimaryCategory(),
            c.getPrimaryConfidence(), c.getAllCategories(), c.getSummary(),
            c.getIsRelevant(), c.getRelevanceConfidence(), c.getCreatedAt()
        );
    }
}
