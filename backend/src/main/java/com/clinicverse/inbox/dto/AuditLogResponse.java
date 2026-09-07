package com.clinicverse.inbox.dto;

import com.clinicverse.inbox.entity.AuditLog;
import java.time.Instant;

public record AuditLogResponse(
    Long id,
    Long emailId,
    String action,
    String actorId,
    String details,
    String source,
    Instant timestamp
) {
    public static AuditLogResponse fromEntity(AuditLog a) {
        String source = extractSource(a.getActorId());
        return new AuditLogResponse(
            a.getId(), a.getEmailId(), a.getAction(),
            a.getActorId(), a.getDetails(), source, a.getTimestamp()
        );
    }

    private static String extractSource(String actorId) {
        if (actorId == null) return "system";
        if (actorId.startsWith("imap")) return "imap";
        if (actorId.startsWith("ai")) return "ai-service";
        if (actorId.startsWith("reviewer") || actorId.startsWith("admin")) return "reviewer";
        if (actorId.equals("system")) return "system";
        return "system";
    }
}
