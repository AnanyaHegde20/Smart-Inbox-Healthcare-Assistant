package com.clinicverse.inbox.repository;

import com.clinicverse.inbox.entity.Extraction;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ExtractionRepository extends JpaRepository<Extraction, Long> {
    Optional<Extraction> findByEmailId(Long emailId);
}
