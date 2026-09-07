package com.clinicverse.inbox.entity;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "audit_logs")
public class AuditLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "email_id")
    private Long emailId;

    @Column(nullable = false)
    private String action;

    @Column(name = "actor_id")
    private String actorId;

    @Column(columnDefinition = "TEXT")
    private String details;

    @Column(nullable = false)
    private Instant timestamp = Instant.now();

    public AuditLog() {}

    public AuditLog(Long emailId, String action, String actorId, String details) {
        this.emailId = emailId;
        this.action = action;
        this.actorId = actorId;
        this.details = details;
    }

    public AuditLog(Long emailId, String action, String actorId, String details, Instant timestamp) {
        this.emailId = emailId;
        this.action = action;
        this.actorId = actorId;
        this.details = details;
        this.timestamp = timestamp;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Long getEmailId() { return emailId; }
    public void setEmailId(Long emailId) { this.emailId = emailId; }

    public String getAction() { return action; }
    public void setAction(String action) { this.action = action; }

    public String getActorId() { return actorId; }
    public void setActorId(String actorId) { this.actorId = actorId; }

    public String getDetails() { return details; }
    public void setDetails(String details) { this.details = details; }

    public Instant getTimestamp() { return timestamp; }
    public void setTimestamp(Instant timestamp) { this.timestamp = timestamp; }
}
