package com.clinicverse.inbox.imap;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class MockEmailProviderTest {

    private MockEmailProvider provider;

    @BeforeEach
    void setUp() {
        provider = new MockEmailProvider();
    }

    @Test
    void connected_afterConnect() {
        assertFalse(provider.isConnected());
        provider.connect();
        assertTrue(provider.isConnected());
        provider.disconnect();
        assertFalse(provider.isConnected());
    }

    @Test
    void fetchNewEmails_returnsEnqueuedThenClears() {
        EmailMessage msg1 = MockEmailProvider.safetyReportEmail();
        EmailMessage msg2 = MockEmailProvider.spamEmail();

        provider.enqueueEmail(msg1);
        provider.enqueueEmail(msg2);

        List<EmailMessage> fetched = provider.fetchNewEmails();
        assertEquals(2, fetched.size());
        assertEquals("msg-safety-001", fetched.get(0).messageId());
        assertEquals("msg-spam-004", fetched.get(1).messageId());

        // Second fetch is empty
        List<EmailMessage> secondFetch = provider.fetchNewEmails();
        assertTrue(secondFetch.isEmpty());
    }

    @Test
    void fetchNewEmails_emptyWhenNothingEnqueued() {
        assertTrue(provider.fetchNewEmails().isEmpty());
    }

    @Test
    void markProcessed_tracksIds() {
        provider.markProcessed("msg-1");
        provider.markProcessed("msg-2");

        List<String> ids = provider.getProcessedIds();
        assertEquals(2, ids.size());
        assertTrue(ids.contains("msg-1"));
        assertTrue(ids.contains("msg-2"));
    }

    @Test
    void clearPending_removesAllPending() {
        provider.enqueueEmail(MockEmailProvider.safetyReportEmail());
        provider.enqueueEmail(MockEmailProvider.spamEmail());
        provider.clearPending();

        assertTrue(provider.fetchNewEmails().isEmpty());
    }

    // --- Factory method tests ---

    @Test
    void safetyReportEmail_hasCorrectFields() {
        EmailMessage msg = MockEmailProvider.safetyReportEmail();
        assertEquals("msg-safety-001", msg.messageId());
        assertEquals("nurse@hospital.org", msg.sender());
        assertEquals("URGENT: Patient Fall Incident Report", msg.subject());
        assertNotNull(msg.receivedAt());
        assertFalse(msg.bodyText().isEmpty());
        assertFalse(msg.attachments().isEmpty());
        assertTrue(msg.attachments().get(0).isPdf());
    }

    @Test
    void qualityComplaintEmail_hasCorrectFields() {
        EmailMessage msg = MockEmailProvider.qualityComplaintEmail();
        assertEquals("msg-complaint-002", msg.messageId());
        assertTrue(msg.attachments().get(0).isPdf());
    }

    @Test
    void infoRequestEmail_hasNoAttachments() {
        EmailMessage msg = MockEmailProvider.infoRequestEmail();
        assertTrue(msg.attachments().isEmpty());
        assertFalse(msg.bodyText().isEmpty());
    }

    @Test
    void spamEmail_hasCorrectFields() {
        EmailMessage msg = MockEmailProvider.spamEmail();
        assertEquals("msg-spam-004", msg.messageId());
        assertTrue(msg.attachments().isEmpty());
        assertTrue(msg.subject().contains("FREE"));
    }

    @Test
    void mixedAttachments_separatesPdfAndNonPdf() {
        EmailMessage msg = MockEmailProvider.emailWithMixedAttachments();
        assertEquals(3, msg.attachments().size());

        long pdfCount = msg.attachments().stream().filter(EmailMessage.Attachment::isPdf).count();
        long nonPdfCount = msg.attachments().stream().filter(a -> !a.isPdf()).count();
        assertEquals(1, pdfCount);
        assertEquals(2, nonPdfCount);
    }

    @Test
    void attachment_isPdf_detectsCorrectly() {
        EmailMessage.Attachment pdf = new EmailMessage.Attachment("report.pdf", "application/pdf", new byte[0], 0);
        EmailMessage.Attachment txt = new EmailMessage.Attachment("notes.txt", "text/plain", new byte[0], 0);
        EmailMessage.Attachment noExt = new EmailMessage.Attachment(null, "application/octet-stream", new byte[0], 0);

        assertTrue(pdf.isPdf());
        assertFalse(txt.isPdf());
        assertFalse(noExt.isPdf());
    }

    @Test
    void emptyBodyEmail_hasEmptyContent() {
        EmailMessage msg = MockEmailProvider.emptyBodyEmail();
        assertTrue(msg.bodyText().isEmpty());
        assertTrue(msg.bodyHtml().isEmpty());
        assertTrue(msg.attachments().isEmpty());
    }
}
