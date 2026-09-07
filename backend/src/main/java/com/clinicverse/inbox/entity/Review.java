package com.clinicverse.inbox.entity;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "reviews")
public class Review {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "email_id", nullable = false, unique = true)
    private Email email;

    @Column(name = "reviewer_id", nullable = false)
    private String reviewerId;

    @Column(nullable = false)
    @Enumerated(EnumType.STRING)
    private ReviewAction action;

    @Column(name = "original_category")
    private String originalCategory;

    @Column(name = "original_confidence")
    private Double originalConfidence;

    @Column(name = "overridden_category")
    private String overriddenCategory;

    @Column(name = "final_category", nullable = false)
    private String finalCategory;

    @Column(columnDefinition = "TEXT")
    private String notes;

    @Column(name = "reviewed_at", nullable = false)
    private Instant reviewedAt = Instant.now();

    public enum ReviewAction {
        ACCEPTED, OVERRIDDEN
    }

    public Review() {}

    public Review(Email email, String reviewerId, ReviewAction action) {
        this.email = email;
        this.reviewerId = reviewerId;
        this.action = action;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Email getEmail() { return email; }
    public void setEmail(Email email) { this.email = email; }

    public String getReviewerId() { return reviewerId; }
    public void setReviewerId(String reviewerId) { this.reviewerId = reviewerId; }

    public ReviewAction getAction() { return action; }
    public void setAction(ReviewAction action) { this.action = action; }

    public String getOriginalCategory() { return originalCategory; }
    public void setOriginalCategory(String originalCategory) { this.originalCategory = originalCategory; }

    public Double getOriginalConfidence() { return originalConfidence; }
    public void setOriginalConfidence(Double originalConfidence) { this.originalConfidence = originalConfidence; }

    public String getOverriddenCategory() { return overriddenCategory; }
    public void setOverriddenCategory(String overriddenCategory) { this.overriddenCategory = overriddenCategory; }

    public String getFinalCategory() { return finalCategory; }
    public void setFinalCategory(String finalCategory) { this.finalCategory = finalCategory; }

    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }

    public Instant getReviewedAt() { return reviewedAt; }
    public void setReviewedAt(Instant reviewedAt) { this.reviewedAt = reviewedAt; }
}
