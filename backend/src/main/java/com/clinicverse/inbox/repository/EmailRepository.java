package com.clinicverse.inbox.repository;

import com.clinicverse.inbox.entity.Email;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface EmailRepository extends JpaRepository<Email, Long> {
    List<Email> findAllByOrderByReceivedAtDesc();
    List<Email> findByStatus(Email.ProcessingStatus status);
}
