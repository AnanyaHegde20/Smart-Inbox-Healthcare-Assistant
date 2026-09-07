package com.clinicverse.inbox.repository;

import com.clinicverse.inbox.entity.Review;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface ReviewRepository extends JpaRepository<Review, Long> {
    Optional<Review> findByEmailId(Long emailId);
    List<Review> findAllByOrderByReviewedAtDesc();
    List<Review> findByReviewerIdOrderByReviewedAtDesc(String reviewerId);
    List<Review> findByActionOrderByReviewedAtDesc(Review.ReviewAction action);
    boolean existsByEmailId(Long emailId);
}
