package com.clinicverse.inbox.repository;

import com.clinicverse.inbox.entity.AuditLog;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface AuditLogRepository extends JpaRepository<AuditLog, Long> {
    List<AuditLog> findAllByOrderByTimestampDesc();
    List<AuditLog> findByEmailIdOrderByTimestampDesc(Long emailId);
    List<AuditLog> findByActionOrderByTimestampDesc(String action);
    List<AuditLog> findByEmailIdAndActionOrderByTimestampDesc(Long emailId, String action);
    long countByAction(String action);
}
