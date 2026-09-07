package com.clinicverse.inbox.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import java.time.Instant;

public record CreateEmailRequest(
    @NotBlank String subject,
    @NotBlank @Email String sender,
    @NotBlank @Email String recipient,
    String body,
    @NotBlank String textContent,
    Instant receivedAt
) {
    public CreateEmailRequest {
        if (receivedAt == null) receivedAt = Instant.now();
    }
}
