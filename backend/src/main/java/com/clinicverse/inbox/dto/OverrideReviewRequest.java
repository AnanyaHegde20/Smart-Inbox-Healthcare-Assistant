package com.clinicverse.inbox.dto;

import jakarta.validation.constraints.NotBlank;

public record OverrideReviewRequest(
    @NotBlank String reviewerId,
    @NotBlank String overriddenCategory,
    String notes
) {}
