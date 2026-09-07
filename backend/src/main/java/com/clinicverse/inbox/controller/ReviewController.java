package com.clinicverse.inbox.controller;

import com.clinicverse.inbox.dto.AcceptReviewRequest;
import com.clinicverse.inbox.dto.OverrideReviewRequest;
import com.clinicverse.inbox.dto.ReviewResponse;
import com.clinicverse.inbox.entity.Review;
import com.clinicverse.inbox.service.ReviewService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/reviews")
public class ReviewController {

    private final ReviewService reviewService;

    public ReviewController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @GetMapping
    public ResponseEntity<List<ReviewResponse>> listAllReviews() {
        return ResponseEntity.ok(reviewService.listAllReviews());
    }

    @GetMapping("/email/{emailId}")
    public ResponseEntity<ReviewResponse> getReview(@PathVariable Long emailId) {
        return ResponseEntity.ok(reviewService.getReview(emailId));
    }

    @GetMapping("/reviewer/{reviewerId}")
    public ResponseEntity<List<ReviewResponse>> getReviewsByReviewer(
            @PathVariable String reviewerId) {
        return ResponseEntity.ok(reviewService.getReviewsByReviewer(reviewerId));
    }

    @PostMapping("/{id}/accept")
    public ResponseEntity<Map<String, Object>> acceptReview(
            @PathVariable Long id,
            @Valid @RequestBody AcceptReviewRequest request) {
        Review review = reviewService.acceptReview(id, request);
        return ResponseEntity.ok(Map.of(
            "id", review.getId(),
            "action", "ACCEPTED",
            "originalCategory", review.getOriginalCategory() != null ? review.getOriginalCategory() : "",
            "originalConfidence", review.getOriginalConfidence() != null ? review.getOriginalConfidence() : 0.0,
            "finalCategory", review.getFinalCategory(),
            "message", "Classification accepted"
        ));
    }

    @PostMapping("/{id}/override")
    public ResponseEntity<Map<String, Object>> overrideReview(
            @PathVariable Long id,
            @Valid @RequestBody OverrideReviewRequest request) {
        Review review = reviewService.overrideReview(id, request);
        return ResponseEntity.ok(Map.of(
            "id", review.getId(),
            "action", "OVERRIDDEN",
            "originalCategory", review.getOriginalCategory() != null ? review.getOriginalCategory() : "",
            "originalConfidence", review.getOriginalConfidence() != null ? review.getOriginalConfidence() : 0.0,
            "overriddenCategory", request.overriddenCategory(),
            "finalCategory", review.getFinalCategory(),
            "message", "Classification overridden"
        ));
    }
}
