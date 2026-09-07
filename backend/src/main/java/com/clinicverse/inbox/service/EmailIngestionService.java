package com.clinicverse.inbox.service;

import com.clinicverse.inbox.entity.AuditAction;
import com.clinicverse.inbox.entity.AuditLog;
import com.clinicverse.inbox.entity.Document;
import com.clinicverse.inbox.entity.Email;
import com.clinicverse.inbox.imap.EmailMessage;
import com.clinicverse.inbox.imap.EmailProvider;
import com.clinicverse.inbox.repository.AuditLogRepository;
import com.clinicverse.inbox.repository.DocumentRepository;
import com.clinicverse.inbox.repository.EmailRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Base64;
import java.util.List;

@Service
public class EmailIngestionService {

    private static final Logger log = LoggerFactory.getLogger(EmailIngestionService.class);

    private final EmailProvider emailProvider;
    private final EmailRepository emailRepo;
    private final DocumentRepository documentRepo;
    private final AiProcessingService aiProcessingService;
    private final AuditLogRepository auditLogRepo;

    public EmailIngestionService(
            EmailProvider emailProvider,
            EmailRepository emailRepo,
            DocumentRepository documentRepo,
            AiProcessingService aiProcessingService,
            AuditLogRepository auditLogRepo) {
        this.emailProvider = emailProvider;
        this.emailRepo = emailRepo;
        this.documentRepo = documentRepo;
        this.aiProcessingService = aiProcessingService;
        this.auditLogRepo = auditLogRepo;
    }

    @Async
    public void pollAndProcess() {
        log.info("Polling IMAP for new emails...");

        if (!emailProvider.isConnected()) {
            log.warn("Email provider not connected; skipping poll");
            return;
        }

        List<EmailMessage> messages = emailProvider.fetchNewEmails();
        log.info("Fetched {} new emails from IMAP", messages.size());

        for (EmailMessage msg : messages) {
            try {
                processEmailMessage(msg);
                emailProvider.markProcessed(msg.messageId());
            } catch (Exception e) {
                log.error("Failed to process email {}: {}", msg.messageId(), e.getMessage());
                // Log failure if we have an email ID
            }
        }
    }

    @Transactional
    public Email processEmailMessage(EmailMessage msg) {
        Email email = new Email(
            msg.subject(),
            msg.sender(),
            "mailbox",
            msg.bodyText(),
            msg.receivedAt()
        );
        email = emailRepo.save(email);

        auditLogRepo.save(new AuditLog(email.getId(), AuditAction.EMAIL_RECEIVED, "imap",
            "From: " + msg.sender() + ", Subject: " + msg.subject()));

        log.info("Email saved: id={}, subject={}, sender={}", email.getId(), msg.subject(), msg.sender());

        // Attach PDF documents for AI processing
        List<EmailMessage.Attachment> pdfAttachments = msg.attachments().stream()
            .filter(EmailMessage.Attachment::isPdf)
            .toList();

        List<EmailMessage.Attachment> nonPdfAttachments = msg.attachments().stream()
            .filter(a -> !a.isPdf())
            .toList();

        // Log non-PDF attachments
        for (EmailMessage.Attachment att : nonPdfAttachments) {
            log.info("Non-PDF attachment (not processed): {} [{}] ({} bytes) on email {}",
                att.filename(), att.contentType(), att.size(), email.getId());
            auditLogRepo.save(new AuditLog(email.getId(), AuditAction.DOCUMENT_RECEIVED, "imap",
                "Non-PDF attachment logged: " + att.filename()
                    + " [" + att.contentType() + "] (" + att.size() + " bytes)"));
        }

        if (!pdfAttachments.isEmpty()) {
            for (EmailMessage.Attachment pdf : pdfAttachments) {
                Document doc = new Document(email, pdf.filename(), pdf.contentType(), pdf.size());
                String base64Content = Base64.getEncoder().encodeToString(pdf.content());
                doc.setExtractedText("[PDF base64 encoded, pending AI extraction]");
                documentRepo.save(doc);

                auditLogRepo.save(new AuditLog(email.getId(), AuditAction.DOCUMENT_RECEIVED, "imap",
                    "PDF attachment: " + pdf.filename()
                        + " [" + pdf.contentType() + "] (" + pdf.size() + " bytes)"));

                log.info("PDF attachment saved: {} on email {}", pdf.filename(), email.getId());
            }

            // Queue async AI processing
            aiProcessingService.processEmailAsync(email.getId());
        } else if (msg.bodyText() != null && !msg.bodyText().isBlank()) {
            // No PDFs, but has body text -- still queue for classification
            aiProcessingService.processEmailAsync(email.getId());
        } else {
            email.setStatus(Email.ProcessingStatus.COMPLETED);
            emailRepo.save(email);
            log.info("Email {} has no processable content; marked COMPLETED", email.getId());
        }

        return email;
    }
}
