package com.clinicverse.inbox.repository;

import com.clinicverse.inbox.entity.Classification;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ClassificationRepository extends JpaRepository<Classification, Long> {
    Optional<Classification> findByEmailId(Long emailId);
}
