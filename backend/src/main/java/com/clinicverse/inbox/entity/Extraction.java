package com.clinicverse.inbox.entity;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "extractions")
public class Extraction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "email_id", nullable = false, unique = true)
    private Email email;

    @Column(name = "extracted_data", columnDefinition = "TEXT", nullable = false)
    private String extractedData;

    @Column(name = "extraction_type")
    private String extractionType;

    @Column(name = "confidence_score")
    private Double confidenceScore;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    public Extraction() {}

    public Extraction(Email email, String extractedData, String extractionType, Double confidenceScore) {
        this.email = email;
        this.extractedData = extractedData;
        this.extractionType = extractionType;
        this.confidenceScore = confidenceScore;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Email getEmail() { return email; }
    public void setEmail(Email email) { this.email = email; }

    public String getExtractedData() { return extractedData; }
    public void setExtractedData(String extractedData) { this.extractedData = extractedData; }

    public String getExtractionType() { return extractionType; }
    public void setExtractionType(String extractionType) { this.extractionType = extractionType; }

    public Double getConfidenceScore() { return confidenceScore; }
    public void setConfidenceScore(Double confidenceScore) { this.confidenceScore = confidenceScore; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
