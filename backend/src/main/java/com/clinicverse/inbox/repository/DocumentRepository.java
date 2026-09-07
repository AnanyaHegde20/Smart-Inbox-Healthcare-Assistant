package com.clinicverse.inbox.repository;

import com.clinicverse.inbox.entity.Document;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface DocumentRepository extends JpaRepository<Document, Long> {
    List<Document> findByEmailId(Long emailId);
}
