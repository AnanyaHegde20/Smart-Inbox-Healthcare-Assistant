package com.clinicverse.inbox.dto;

import com.clinicverse.inbox.entity.Email;
import java.time.Instant;
import java.util.List;

public record EmailResponse(
    Long id,
    String subject,
    String sender,
    String recipient,
    String body,
    Instant receivedAt,
    String status,
    String errorMessage,
    Instant createdAt,
    Instant updatedAt,
    List<DocumentSummary> documents,
    String reviewStatus,
    String finalCategory,
    String reviewedBy,
    Instant reviewedAt
) {
    public record DocumentSummary(Long id, String filename, String contentType, Long fileSize) {}

    public static EmailResponse fromEntity(Email e) {
        var docs = e.getDocuments().stream()
            .map(d -> new DocumentSummary(d.getId(), d.getFilename(), d.getContentType(), d.getFileSize()))
            .toList();

        String reviewStatus = null;
        String finalCategory = null;
        String reviewedBy = null;
        Instant reviewedAtTs = null;

        if (e.getReview() != null) {
            reviewStatus = e.getReview().getAction().name();
            finalCategory = e.getReview().getFinalCategory();
            reviewedBy = e.getReview().getReviewerId();
            reviewedAtTs = e.getReview().getReviewedAt();
        }

        return new EmailResponse(
            e.getId(), e.getSubject(), e.getSender(), e.getRecipient(), e.getBody(),
            e.getReceivedAt(), e.getStatus().name(), e.getErrorMessage(),
            e.getCreatedAt(), e.getUpdatedAt(), docs,
            reviewStatus, finalCategory, reviewedBy, reviewedAtTs
        );
    }
}
