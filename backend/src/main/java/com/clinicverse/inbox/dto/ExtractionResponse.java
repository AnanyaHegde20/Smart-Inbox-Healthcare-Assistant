package com.clinicverse.inbox.dto;

import com.clinicverse.inbox.entity.Extraction;
import java.time.Instant;

public record ExtractionResponse(
    Long id,
    Long emailId,
    String extractedData,
    String extractionType,
    Double confidenceScore,
    Instant createdAt
) {
    public static ExtractionResponse fromEntity(Extraction e) {
        return new ExtractionResponse(
            e.getId(), e.getEmail().getId(), e.getExtractedData(),
            e.getExtractionType(), e.getConfidenceScore(), e.getCreatedAt()
        );
    }
}
