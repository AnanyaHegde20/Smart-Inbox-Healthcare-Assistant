package com.clinicverse.inbox.imap;

import java.util.List;

public interface EmailProvider {

    List<EmailMessage> fetchNewEmails();

    void markProcessed(String messageId);

    boolean isConnected();

    void connect();

    void disconnect();
}
