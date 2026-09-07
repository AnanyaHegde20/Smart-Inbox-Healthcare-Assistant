package com.clinicverse.inbox.entity;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "classifications")
public class Classification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "email_id", nullable = false, unique = true)
    private Email email;

    @Column(name = "primary_category", nullable = false)
    private String primaryCategory;

    @Column(name = "primary_confidence", nullable = false)
    private Double primaryConfidence;

    @Column(name = "all_categories", columnDefinition = "TEXT")
    private String allCategories;

    @Column(columnDefinition = "TEXT")
    private String summary;

    @Column(name = "is_relevant")
    private Boolean isRelevant;

    @Column(name = "relevance_confidence")
    private Double relevanceConfidence;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    public Classification() {}

    public Classification(Email email, String primaryCategory, Double primaryConfidence, String allCategories) {
        this.email = email;
        this.primaryCategory = primaryCategory;
        this.primaryConfidence = primaryConfidence;
        this.allCategories = allCategories;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Email getEmail() { return email; }
    public void setEmail(Email email) { this.email = email; }

    public String getPrimaryCategory() { return primaryCategory; }
    public void setPrimaryCategory(String primaryCategory) { this.primaryCategory = primaryCategory; }

    public Double getPrimaryConfidence() { return primaryConfidence; }
    public void setPrimaryConfidence(Double primaryConfidence) { this.primaryConfidence = primaryConfidence; }

    public String getAllCategories() { return allCategories; }
    public void setAllCategories(String allCategories) { this.allCategories = allCategories; }

    public String getSummary() { return summary; }
    public void setSummary(String summary) { this.summary = summary; }

    public Boolean getIsRelevant() { return isRelevant; }
    public void setIsRelevant(Boolean isRelevant) { this.isRelevant = isRelevant; }

    public Double getRelevanceConfidence() { return relevanceConfidence; }
    public void setRelevanceConfidence(Double relevanceConfidence) { this.relevanceConfidence = relevanceConfidence; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
