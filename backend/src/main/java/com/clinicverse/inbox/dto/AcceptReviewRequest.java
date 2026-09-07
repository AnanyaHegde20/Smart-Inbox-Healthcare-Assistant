package com.clinicverse.inbox.dto;

import jakarta.validation.constraints.NotBlank;

public record AcceptReviewRequest(
    @NotBlank String reviewerId,
    String notes
) {}
