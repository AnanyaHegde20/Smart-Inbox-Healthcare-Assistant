package com.clinicverse.inbox.controller;

import com.clinicverse.inbox.dto.*;
import com.clinicverse.inbox.service.AiProcessingService;
import com.clinicverse.inbox.service.EmailService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/emails")
public class EmailController {

    private final EmailService emailService;
    private final AiProcessingService aiProcessingService;

    public EmailController(EmailService emailService, AiProcessingService aiProcessingService) {
        this.emailService = emailService;
        this.aiProcessingService = aiProcessingService;
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> createEmail(@Valid @RequestBody CreateEmailRequest request) {
        EmailResponse email = emailService.createEmail(request);
        aiProcessingService.processEmailAsync(email.id());
        return ResponseEntity.status(HttpStatus.CREATED).body(Map.of(
            "id", email.id(),
            "status", "RECEIVED",
            "message", "Email received and processing queued"
        ));
    }

    @GetMapping
    public ResponseEntity<List<EmailResponse>> listEmails() {
        return ResponseEntity.ok(emailService.listEmails());
    }

    @GetMapping("/{id}")
    public ResponseEntity<EmailResponse> getEmail(@PathVariable Long id) {
        return ResponseEntity.ok(emailService.getEmail(id));
    }

    @GetMapping("/{id}/documents")
    public ResponseEntity<List<DocumentResponse>> getDocuments(@PathVariable Long id) {
        return ResponseEntity.ok(emailService.getDocuments(id));
    }

    @GetMapping("/{id}/classification")
    public ResponseEntity<ClassificationResponse> getClassification(@PathVariable Long id) {
        return ResponseEntity.ok(emailService.getClassification(id));
    }

    @GetMapping("/{id}/extraction")
    public ResponseEntity<ExtractionResponse> getExtraction(@PathVariable Long id) {
        return ResponseEntity.ok(emailService.getExtraction(id));
    }
}
