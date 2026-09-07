package com.clinicverse.inbox.controller;

import com.clinicverse.inbox.dto.AuditLogResponse;
import com.clinicverse.inbox.service.AuditLogService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/audit-logs")
public class AuditLogController {

    private final AuditLogService auditLogService;

    public AuditLogController(AuditLogService auditLogService) {
        this.auditLogService = auditLogService;
    }

    @GetMapping
    public ResponseEntity<List<AuditLogResponse>> listAuditLogs() {
        return ResponseEntity.ok(auditLogService.listAuditLogs());
    }

    @GetMapping("/email/{emailId}")
    public ResponseEntity<List<AuditLogResponse>> getAuditLogsByEmail(@PathVariable Long emailId) {
        return ResponseEntity.ok(auditLogService.getAuditLogsByEmail(emailId));
    }

    @GetMapping("/action/{action}")
    public ResponseEntity<List<AuditLogResponse>> getAuditLogsByAction(@PathVariable String action) {
        return ResponseEntity.ok(auditLogService.getAuditLogsByAction(action));
    }

    @GetMapping("/email/{emailId}/action/{action}")
    public ResponseEntity<List<AuditLogResponse>> getAuditLogsByEmailAndAction(
            @PathVariable Long emailId, @PathVariable String action) {
        return ResponseEntity.ok(auditLogService.getAuditLogsByEmailAndAction(emailId, action));
    }

    @GetMapping("/stats")
    public ResponseEntity<Map<String, Long>> getAuditStats() {
        return ResponseEntity.ok(auditLogService.getAuditStats());
    }
}
