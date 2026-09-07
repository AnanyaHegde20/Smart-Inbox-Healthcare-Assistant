package com.clinicverse.inbox.imap;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "imap")
public class ImapProperties {

    private String host = "imap.gmail.com";
    private int port = 993;
    private String username = "";
    private String password = "";
    private String folder = "INBOX";
    private boolean ssl = true;
    private boolean deleteAfterFetch = false;
    private int fetchBatchSize = 10;

    public String getHost() { return host; }
    public void setHost(String host) { this.host = host; }

    public int getPort() { return port; }
    public void setPort(int port) { this.port = port; }

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }

    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }

    public String getFolder() { return folder; }
    public void setFolder(String folder) { this.folder = folder; }

    public boolean isSsl() { return ssl; }
    public void setSsl(boolean ssl) { this.ssl = ssl; }

    public boolean isDeleteAfterFetch() { return deleteAfterFetch; }
    public void setDeleteAfterFetch(boolean deleteAfterFetch) { this.deleteAfterFetch = deleteAfterFetch; }

    public int getFetchBatchSize() { return fetchBatchSize; }
    public void setFetchBatchSize(int fetchBatchSize) { this.fetchBatchSize = fetchBatchSize; }
}
