package com.clinicverse.inbox.imap;

import java.time.Instant;
import java.util.List;

public record EmailMessage(
    String messageId,
    String sender,
    String subject,
    Instant receivedAt,
    String bodyText,
    String bodyHtml,
    List<Attachment> attachments
) {
    public record Attachment(
        String filename,
        String contentType,
        byte[] content,
        long size
    ) {
        public boolean isPdf() {
            return filename != null && filename.toLowerCase().endsWith(".pdf");
        }
    }
}
