package com.clinicverse.inbox.service;

import com.clinicverse.inbox.dto.*;
import com.clinicverse.inbox.entity.*;
import com.clinicverse.inbox.exception.ResourceNotFoundException;
import com.clinicverse.inbox.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class EmailService {

    private static final Logger log = LoggerFactory.getLogger(EmailService.class);

    private final EmailRepository emailRepo;
    private final DocumentRepository documentRepo;
    private final AuditLogRepository auditLogRepo;

    public EmailService(EmailRepository emailRepo, DocumentRepository documentRepo,
                        AuditLogRepository auditLogRepo) {
        this.emailRepo = emailRepo;
        this.documentRepo = documentRepo;
        this.auditLogRepo = auditLogRepo;
    }

    @Transactional
    public EmailResponse createEmail(CreateEmailRequest request) {
        Email email = new Email(
            request.subject(),
            request.sender(),
            request.recipient(),
            request.body(),
            request.receivedAt()
        );
        email = emailRepo.save(email);

        auditLogRepo.save(new AuditLog(email.getId(), "EMAIL_RECEIVED", "system",
            "Email received from " + request.sender()));

        log.info("Email created: id={}, subject={}", email.getId(), email.getSubject());
        return EmailResponse.fromEntity(email);
    }

    @Transactional(readOnly = true)
    public List<EmailResponse> listEmails() {
        return emailRepo.findAllByOrderByReceivedAtDesc().stream()
            .map(EmailResponse::fromEntity)
            .toList();
    }

    @Transactional(readOnly = true)
    public EmailResponse getEmail(Long id) {
        Email email = findEmail(id);
        return EmailResponse.fromEntity(email);
    }

    @Transactional(readOnly = true)
    public List<DocumentResponse> getDocuments(Long emailId) {
        findEmail(emailId); // validate exists
        return documentRepo.findByEmailId(emailId).stream()
            .map(DocumentResponse::fromEntity)
            .toList();
    }

    @Transactional(readOnly = true)
    public ClassificationResponse getClassification(Long emailId) {
        Email email = findEmail(emailId);
        Classification c = email.getClassification();
        if (c == null) {
            throw new ResourceNotFoundException("Classification for email", emailId);
        }
        return ClassificationResponse.fromEntity(c);
    }

    @Transactional(readOnly = true)
    public ExtractionResponse getExtraction(Long emailId) {
        Email email = findEmail(emailId);
        Extraction e = email.getExtraction();
        if (e == null) {
            throw new ResourceNotFoundException("Extraction for email", emailId);
        }
        return ExtractionResponse.fromEntity(e);
    }

    Email findEmail(Long id) {
        return emailRepo.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Email", id));
    }
}
