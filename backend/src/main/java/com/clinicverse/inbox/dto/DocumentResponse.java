package com.clinicverse.inbox.dto;

import com.clinicverse.inbox.entity.Document;

public record DocumentResponse(
    Long id,
    Long emailId,
    String filename,
    String contentType,
    Long fileSize,
    String extractedText,
    Boolean ocrUsed,
    Integer pageCount,
    String language
) {
    public static DocumentResponse fromEntity(Document d) {
        return new DocumentResponse(
            d.getId(), d.getEmail().getId(), d.getFilename(), d.getContentType(),
            d.getFileSize(), d.getExtractedText(), d.getOcrUsed(),
            d.getPageCount(), d.getLanguage()
        );
    }
}
