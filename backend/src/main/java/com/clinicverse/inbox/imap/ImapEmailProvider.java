package com.clinicverse.inbox.imap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import jakarta.mail.*;
import jakarta.mail.internet.MimeMultipart;
import java.io.IOException;
import java.io.InputStream;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Properties;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class ImapEmailProvider implements EmailProvider {

    private static final Logger log = LoggerFactory.getLogger(ImapEmailProvider.class);

    private final ImapProperties properties;
    private Session session;
    private Store store;
    private Folder folder;
    private final Set<String> processedIds = ConcurrentHashMap.newKeySet();

    public ImapEmailProvider(ImapProperties properties) {
        this.properties = properties;
    }

    @PostConstruct
    public void init() {
        if (properties.getUsername() != null && !properties.getUsername().isEmpty()) {
            try {
                connect();
            } catch (Exception e) {
                log.warn("IMAP auto-connect failed (will retry on first fetch): {}", e.getMessage());
            }
        } else {
            log.info("IMAP credentials not configured; provider will not auto-connect");
        }
    }

    @PreDestroy
    public void cleanup() {
        disconnect();
    }

    @Override
    public void connect() {
        try {
            Properties props = new Properties();
            props.put("mail.store.protocol", "imap");
            props.put("mail.imap.host", properties.getHost());
            props.put("mail.imap.port", String.valueOf(properties.getPort()));
            props.put("mail.imap.ssl.enable", String.valueOf(properties.isSsl()));
            props.put("mail.imap.connectiontimeout", "10000");
            props.put("mail.imap.timeout", "15000");
            props.put("mail.imap.partialfetch", "false");

            session = Session.getInstance(props);
            store = session.getStore("imap");
            store.connect(properties.getHost(), properties.getUsername(), properties.getPassword());

            folder = store.getFolder(properties.getFolder());
            folder.open(Folder.READ_WRITE);

            log.info("IMAP connected to {}:{}/{}", properties.getHost(), properties.getPort(), properties.getFolder());
        } catch (Exception e) {
            log.error("IMAP connection failed: {}", e.getMessage());
            throw new RuntimeException("IMAP connection failed", e);
        }
    }

    @Override
    public void disconnect() {
        try {
            if (folder != null && folder.isOpen()) folder.close(true);
            if (store != null) store.close();
            log.info("IMAP disconnected");
        } catch (Exception e) {
            log.warn("IMAP disconnect error: {}", e.getMessage());
        }
    }

    @Override
    public boolean isConnected() {
        try {
            return store != null && store.isConnected() && folder != null && folder.isOpen();
        } catch (Exception e) {
            return false;
        }
    }

    @Override
    public List<EmailMessage> fetchNewEmails() {
        if (!isConnected()) {
            log.info("IMAP not connected; attempting to connect...");
            try {
                connect();
            } catch (Exception e) {
                log.error("Cannot connect to IMAP: {}", e.getMessage());
                return List.of();
            }
        }

        List<EmailMessage> messages = new ArrayList<>();
        try {
            Message[] folderMessages = folder.getMessages();
            int fetchCount = Math.min(folderMessages.length, properties.getFetchBatchSize());

            if (fetchCount == 0) {
                return List.of();
            }

            log.info("Found {} messages in mailbox, fetching up to {}", folderMessages.length, fetchCount);

            for (int i = folderMessages.length - 1; i >= Math.max(0, folderMessages.length - fetchCount); i--) {
                Message msg = folderMessages[i];
                String messageId = extractMessageId(msg);

                if (processedIds.contains(messageId)) {
                    continue;
                }

                try {
                    EmailMessage parsed = parseMessage(msg, messageId);
                    messages.add(parsed);
                } catch (Exception e) {
                    log.warn("Failed to parse message {}: {}", messageId, e.getMessage());
                }
            }
        } catch (Exception e) {
            log.error("Error fetching IMAP messages: {}", e.getMessage());
        }

        return messages;
    }

    @Override
    public void markProcessed(String messageId) {
        processedIds.add(messageId);
    }

    private EmailMessage parseMessage(Message msg, String messageId) throws MessagingException, IOException {
        String sender = extractSender(msg);
        String subject = msg.getSubject();
        Instant receivedAt = msg.getSentDate() != null ? msg.getSentDate().toInstant() : Instant.now();
        String bodyText = extractTextBody(msg);
        String bodyHtml = extractHtmlBody(msg);
        List<EmailMessage.Attachment> attachments = extractAttachments(msg);

        return new EmailMessage(messageId, sender, subject, receivedAt, bodyText, bodyHtml, attachments);
    }

    private String extractMessageId(Message msg) {
        try {
            String[] ids = msg.getHeader("Message-ID");
            if (ids != null && ids.length > 0) {
                return ids[0];
            }
        } catch (MessagingException e) {
            // fallback
        }
        return "msg-" + System.identityHashCode(msg);
    }

    private String extractSender(Message msg) {
        try {
            Address[] from = msg.getFrom();
            if (from != null && from.length > 0) {
                return from[0].toString();
            }
        } catch (MessagingException e) {
            log.warn("Error extracting sender: {}", e.getMessage());
        }
        return "unknown";
    }

    private String extractTextBody(Message msg) throws MessagingException, IOException {
        Object content = msg.getContent();
        if (content instanceof String) {
            return (String) content;
        }
        if (content instanceof MimeMultipart) {
            return extractTextFromMultipart((MimeMultipart) content);
        }
        return "";
    }

    private String extractHtmlBody(Message msg) throws MessagingException, IOException {
        Object content = msg.getContent();
        if (content instanceof MimeMultipart) {
            return extractHtmlFromMultipart((MimeMultipart) content);
        }
        return "";
    }

    private String extractTextFromMultipart(MimeMultipart multipart) throws MessagingException, IOException {
        for (int i = 0; i < multipart.getCount(); i++) {
            BodyPart bodyPart = multipart.getBodyPart(i);
            String contentType = bodyPart.getContentType().toLowerCase();

            if (contentType.startsWith("text/plain")) {
                return (String) bodyPart.getContent();
            }

            if (bodyPart.getContent() instanceof MimeMultipart) {
                String nested = extractTextFromMultipart((MimeMultipart) bodyPart.getContent());
                if (!nested.isEmpty()) return nested;
            }
        }
        return "";
    }

    private String extractHtmlFromMultipart(MimeMultipart multipart) throws MessagingException, IOException {
        for (int i = 0; i < multipart.getCount(); i++) {
            BodyPart bodyPart = multipart.getBodyPart(i);
            String contentType = bodyPart.getContentType().toLowerCase();

            if (contentType.startsWith("text/html")) {
                return (String) bodyPart.getContent();
            }

            if (bodyPart.getContent() instanceof MimeMultipart) {
                String nested = extractHtmlFromMultipart((MimeMultipart) bodyPart.getContent());
                if (!nested.isEmpty()) return nested;
            }
        }
        return "";
    }

    private List<EmailMessage.Attachment> extractAttachments(Message msg) throws MessagingException, IOException {
        List<EmailMessage.Attachment> attachments = new ArrayList<>();
        Object content = msg.getContent();

        if (content instanceof MimeMultipart) {
            extractAttachmentsFromMultipart((MimeMultipart) content, attachments);
        }

        return attachments;
    }

    private void extractAttachmentsFromMultipart(MimeMultipart multipart, List<EmailMessage.Attachment> attachments)
            throws MessagingException, IOException {
        for (int i = 0; i < multipart.getCount(); i++) {
            BodyPart bodyPart = multipart.getBodyPart(i);

            if (Part.ATTACHMENT.equalsIgnoreCase(bodyPart.getDisposition()) ||
                (bodyPart.getFileName() != null && !bodyPart.getFileName().isEmpty())) {

                String filename = bodyPart.getFileName();
                String contentType = bodyPart.getContentType();
                long size = bodyPart.getSize();

                try (InputStream is = bodyPart.getInputStream()) {
                    byte[] contentBytes = is.readAllBytes();
                    attachments.add(new EmailMessage.Attachment(filename, contentType, contentBytes, size));
                }

                if (filename != null && filename.toLowerCase().endsWith(".pdf")) {
                    log.info("PDF attachment found: {} ({} bytes)", filename, size);
                } else {
                    log.info("Non-PDF attachment logged (not processed): {} [{}] ({} bytes)",
                        filename, contentType, size);
                }
            }

            if (bodyPart.getContent() instanceof MimeMultipart) {
                extractAttachmentsFromMultipart((MimeMultipart) bodyPart.getContent(), attachments);
            }
        }
    }
}
