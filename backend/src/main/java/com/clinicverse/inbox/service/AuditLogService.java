package com.clinicverse.inbox.service;

import com.clinicverse.inbox.dto.AuditLogResponse;
import com.clinicverse.inbox.repository.AuditLogRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class AuditLogService {

    private final AuditLogRepository auditLogRepo;

    public AuditLogService(AuditLogRepository auditLogRepo) {
        this.auditLogRepo = auditLogRepo;
    }

    @Transactional(readOnly = true)
    public List<AuditLogResponse> listAuditLogs() {
        return auditLogRepo.findAllByOrderByTimestampDesc().stream()
            .map(AuditLogResponse::fromEntity)
            .toList();
    }

    @Transactional(readOnly = true)
    public List<AuditLogResponse> getAuditLogsByEmail(Long emailId) {
        return auditLogRepo.findByEmailIdOrderByTimestampDesc(emailId).stream()
            .map(AuditLogResponse::fromEntity)
            .toList();
    }

    @Transactional(readOnly = true)
    public List<AuditLogResponse> getAuditLogsByAction(String action) {
        return auditLogRepo.findByActionOrderByTimestampDesc(action).stream()
            .map(AuditLogResponse::fromEntity)
            .toList();
    }

    @Transactional(readOnly = true)
    public List<AuditLogResponse> getAuditLogsByEmailAndAction(Long emailId, String action) {
        return auditLogRepo.findByEmailIdAndActionOrderByTimestampDesc(emailId, action).stream()
            .map(AuditLogResponse::fromEntity)
            .toList();
    }

    @Transactional(readOnly = true)
    public Map<String, Long> getAuditStats() {
        return auditLogRepo.findAll().stream()
            .collect(Collectors.groupingBy(
                com.clinicverse.inbox.entity.AuditLog::getAction,
                Collectors.counting()
            ));
    }
}
