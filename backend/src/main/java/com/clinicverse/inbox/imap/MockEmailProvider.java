package com.clinicverse.inbox.imap;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Queue;
import java.util.concurrent.ConcurrentLinkedQueue;

public class MockEmailProvider implements EmailProvider {

    private final Queue<EmailMessage> pendingEmails = new ConcurrentLinkedQueue<>();
    private final List<String> processedIds = new ArrayList<>();
    private boolean connected = false;

    @Override
    public List<EmailMessage> fetchNewEmails() {
        List<EmailMessage> batch = new ArrayList<>();
        EmailMessage msg;
        while ((msg = pendingEmails.poll()) != null) {
            batch.add(msg);
        }
        return batch;
    }

    @Override
    public void markProcessed(String messageId) {
        processedIds.add(messageId);
    }

    @Override
    public boolean isConnected() {
        return connected;
    }

    @Override
    public void connect() {
        connected = true;
    }

    @Override
    public void disconnect() {
        connected = false;
    }

    // --- Test helpers ---

    public void enqueueEmail(EmailMessage message) {
        pendingEmails.add(message);
    }

    public void clearPending() {
        pendingEmails.clear();
    }

    public List<String> getProcessedIds() {
        return List.copyOf(processedIds);
    }

    // --- Static factory methods for common test scenarios ---

    public static EmailMessage safetyReportEmail() {
        return new EmailMessage(
            "msg-safety-001",
            "nurse@hospital.org",
            "URGENT: Patient Fall Incident Report",
            Instant.parse("2025-06-15T10:30:00Z"),
            "Patient fall incident report attached. Patient Test Subject Alpha fell in Room 302.",
            "<p>Patient fall incident report attached.</p>",
            List.of(new EmailMessage.Attachment("incident_report.pdf", "application/pdf",
                "%PDF-1.4 fake pdf content".getBytes(StandardCharsets.UTF_8), 1024))
        );
    }

    public static EmailMessage qualityComplaintEmail() {
        return new EmailMessage(
            "msg-complaint-002",
            "complainant@test.com",
            "Quality Complaint - Blood Pressure Monitor",
            Instant.parse("2025-07-20T14:00:00Z"),
            "The blood pressure monitor gives inconsistent readings. Complaint form attached.",
            "<p>Complaint form attached.</p>",
            List.of(new EmailMessage.Attachment("complaint.pdf", "application/pdf",
                "%PDF-1.4 fake pdf content".getBytes(StandardCharsets.UTF_8), 2048))
        );
    }

    public static EmailMessage infoRequestEmail() {
        return new EmailMessage(
            "msg-request-003",
            "requester@clinic.org",
            "Information Request - Medication Storage",
            Instant.parse("2025-08-01T09:15:00Z"),
            "What is the proper storage temperature for Insulin Glargine?",
            "<p>What is the proper storage temperature for Insulin Glargine?</p>",
            List.of()
        );
    }

    public static EmailMessage spamEmail() {
        return new EmailMessage(
            "msg-spam-004",
            "winner@lottery.com",
            "You've Won a FREE Vacation!",
            Instant.parse("2025-08-05T12:00:00Z"),
            "Congratulations! Click here to claim your free trip.",
            "<p>Congratulations! Click here to claim your free trip.</p>",
            List.of()
        );
    }

    public static EmailMessage emailWithMixedAttachments() {
        return new EmailMessage(
            "msg-mixed-005",
            "records@hospital.org",
            "Patient Records Update",
            Instant.parse("2025-08-10T11:00:00Z"),
            "Please find attached records and reference document.",
            "<p>Please find attached records.</p>",
            List.of(
                new EmailMessage.Attachment("patient_record.pdf", "application/pdf",
                    "%PDF-1.4 fake pdf content".getBytes(StandardCharsets.UTF_8), 3072),
                new EmailMessage.Attachment("reference_image.png", "image/png",
                    new byte[]{0, 1, 2, 3, 4, 5}, 6),
                new EmailMessage.Attachment("data_export.csv", "text/csv",
                    "name,value\ntest,123".getBytes(StandardCharsets.UTF_8), 19)
            )
        );
    }

    public static EmailMessage emptyBodyEmail() {
        return new EmailMessage(
            "msg-empty-006",
            "sender@test.com",
            "Blank Email",
            Instant.parse("2025-08-15T08:00:00Z"),
            "",
            "",
            List.of()
        );
    }
}
