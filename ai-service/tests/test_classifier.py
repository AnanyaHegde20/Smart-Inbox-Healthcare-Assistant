"""Tests for the multi-category classifier.

Covers all four categories, multi-category scenarios, edge cases,
and structured JSON output validation.

All test data is synthetic — no real patient information.
"""

from __future__ import annotations

import json

import pytest

from app.classifier import classify, Category, CategoryResult, ClassificationResult
from app.models.responses import CategoryOutput, ClassificationOutput
from app.classifier.rules import _score_category, _SAFETY_KEYWORDS, _QUALITY_KEYWORDS


# ---------------------------------------------------------------------------
# SAFETY_REPORT tests
# ---------------------------------------------------------------------------

class TestSafetyReport:
    def test_adverse_event(self):
        result = classify("Patient experienced an adverse event after medication administration.")
        assert result.has_category(Category.SAFETY_REPORT)
        cat = result.get(Category.SAFETY_REPORT)
        assert cat.confidence > 0.15
        assert "adverse" in cat.reason.lower()

    def test_patient_fall(self):
        result = classify("Incident report: Patient fall in room 302 at 02:15 AM.")
        assert result.has_category(Category.SAFETY_REPORT)
        assert result.get(Category.SAFETY_REPORT).confidence > 0.25

    def test_medication_error(self):
        result = classify("Medication error: patient received wrong dose of insulin.")
        assert result.has_category(Category.SAFETY_REPORT)
        assert result.get(Category.SAFETY_REPORT).confidence > 0.3

    def test_sentinel_event(self):
        result = classify("This is a sentinel event. Wrong site surgery performed on patient.")
        assert result.has_category(Category.SAFETY_REPORT)
        assert result.get(Category.SAFETY_REPORT).confidence > 0.4

    def test_device_failure(self):
        result = classify("Device failure: ventilator stopped functioning during night shift.")
        assert result.has_category(Category.SAFETY_REPORT)

    def test_infection_reported(self):
        result = classify("Hospital-acquired infection reported in ward 4. Two patients affected.")
        assert result.has_category(Category.SAFETY_REPORT)

    def test_safety_context_boosts(self):
        text = "Patient safety incident report filed for the fall that occurred last night."
        result = classify(text)
        assert result.has_category(Category.SAFETY_REPORT)
        assert result.get(Category.SAFETY_REPORT).confidence > 0.3


# ---------------------------------------------------------------------------
# QUALITY_COMPLAINT tests
# ---------------------------------------------------------------------------

class TestQualityComplaint:
    def test_direct_complaint(self):
        result = classify("I want to file a complaint about the poor service I received.")
        assert result.has_category(Category.QUALITY_COMPLAINT)
        cat = result.get(Category.QUALITY_COMPLAINT)
        assert cat.confidence > 0.25

    def test_wait_time_complaint(self):
        result = classify("I waited 3 hours in the emergency room. This is unacceptable.")
        assert result.has_category(Category.QUALITY_COMPLAINT)

    def test_unprofessional_behavior(self):
        result = classify("The nurse was rude and unprofessional during my stay.")
        assert result.has_category(Category.QUALITY_COMPLAINT)

    def test_cleanliness_complaint(self):
        result = classify("The room was dirty and unclean when I arrived.")
        assert result.has_category(Category.QUALITY_COMPLAINT)

    def test_billing_complaint(self):
        result = classify("I was overcharged for the procedure. Billing complaint filed.")
        assert result.has_category(Category.QUALITY_COMPLAINT)

    def test_premature_discharge(self):
        result = classify("I was discharged too early and my symptoms returned.")
        assert result.has_category(Category.QUALITY_COMPLAINT)

    def test_dissatisfied_patient(self):
        result = classify("Patient is dissatisfied with the quality of care received.")
        assert result.has_category(Category.QUALITY_COMPLAINT)


# ---------------------------------------------------------------------------
# INFO_REQUEST tests
# ---------------------------------------------------------------------------

class TestInfoRequest:
    def test_question_mark(self):
        result = classify("What are the visiting hours at the hospital?")
        assert result.has_category(Category.INFO_REQUEST)
        cat = result.get(Category.INFO_REQUEST)
        assert cat.confidence > 0.1

    def test_please_provide(self):
        result = classify("Could you please provide copies of my medical records?")
        assert result.has_category(Category.INFO_REQUEST)

    def test_status_update(self):
        result = classify("Request for status update on my pending lab results.")
        assert result.has_category(Category.INFO_REQUEST)

    def test_results_request(self):
        result = classify("Can you send me my test results from last week?")
        assert result.has_category(Category.INFO_REQUEST)

    def test_referral_request(self):
        result = classify("I need a referral to a cardiologist. Please advise.")
        assert result.has_category(Category.INFO_REQUEST)

    def test_appointment_inquiry(self):
        result = classify("What is the availability for an appointment next Tuesday?")
        assert result.has_category(Category.INFO_REQUEST)

    def test_need_clarification(self):
        result = classify("I need clarification on the discharge instructions provided.")
        assert result.has_category(Category.INFO_REQUEST)


# ---------------------------------------------------------------------------
# NOT_RELEVANT tests
# ---------------------------------------------------------------------------

class TestNotRelevant:
    def test_spam_email(self):
        result = classify("Congratulations! You have won a free vacation. Click here to claim.")
        assert result.has_category(Category.NOT_RELEVANT)

    def test_marketing(self):
        result = classify("Subscribe to our weekly newsletter for health tips and promotions.")
        assert result.has_category(Category.NOT_RELEVANT)

    def test_pharmacy_spam(self):
        result = classify("Discount viagra and cialis available. Buy now at our online pharmacy.")
        assert result.has_category(Category.NOT_RELEVANT)

    def test_lottery_scam(self):
        result = classify("Dear friend, you are the lucky winner of our lottery prize!")
        assert result.has_category(Category.NOT_RELEVANT)

    def test_unrelated_content(self):
        result = classify("The weather forecast for tomorrow shows sunny skies with a high of 75F.")
        assert result.has_category(Category.NOT_RELEVANT)


# ---------------------------------------------------------------------------
# Multi-category tests
# ---------------------------------------------------------------------------

class TestMultiCategory:
    def test_safety_and_quality(self):
        text = (
            "Patient fell in the bathroom resulting in an injury. "
            "I want to file a complaint about the poor safety measures. "
            "The staff was unprofessional and did not respond promptly."
        )
        result = classify(text)
        assert result.has_category(Category.SAFETY_REPORT)
        assert result.has_category(Category.QUALITY_COMPLAINT)
        # Both should have meaningful confidence
        assert result.get(Category.SAFETY_REPORT).confidence > 0.2
        assert result.get(Category.QUALITY_COMPLAINT).confidence > 0.2

    def test_info_request_with_complaint(self):
        text = (
            "I am writing to complain about the long wait time. "
            "Can you also provide information about your complaint process?"
        )
        result = classify(text)
        assert result.has_category(Category.QUALITY_COMPLAINT)
        assert result.has_category(Category.INFO_REQUEST)

    def test_safety_and_info(self):
        text = (
            "Adverse event report: medication error in ward 5. "
            "Please provide the incident investigation results."
        )
        result = classify(text)
        assert result.has_category(Category.SAFETY_REPORT)
        assert result.has_category(Category.INFO_REQUEST)

    def test_all_categories_possible(self):
        text = (
            "I need to report a patient fall adverse event (safety report). "
            "The staff was unprofessional (quality complaint). "
            "Can you provide the investigation results? (info request). "
            "This is not a promotional email (not spam)."
        )
        result = classify(text)
        # At least 3 categories should match
        assert len(result.categories) >= 3

    def test_single_category_dominates(self):
        text = "Adverse event: patient experienced cardiac arrest and required resuscitation."
        result = classify(text)
        # SAFETY_REPORT should be primary
        assert result.primary.category == Category.SAFETY_REPORT
        assert result.primary.confidence > 0.2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_text(self):
        result = classify("")
        assert result.has_category(Category.NOT_RELEVANT)
        assert result.get(Category.NOT_RELEVANT).confidence >= 0.9

    def test_whitespace_only(self):
        result = classify("   \n\t  ")
        assert result.has_category(Category.NOT_RELEVANT)

    def test_very_short_text(self):
        result = classify("Hello")
        # Short text should have lower confidence
        assert result.categories[0].confidence < 0.5

    def test_no_match_defaults_to_not_relevant(self):
        result = classify("Random unrelated content with no matching keywords.")
        assert result.has_category(Category.NOT_RELEVANT)

    def test_confidence_range(self):
        result = classify("Patient adverse event with complaint about service quality and request for info.")
        for cat in result.categories:
            assert 0.0 <= cat.confidence <= 1.0

    def test_sorted_by_confidence_desc(self):
        result = classify(
            "Adverse event report. I also have a complaint and a question about results."
        )
        confidences = [c.confidence for c in result.categories]
        assert confidences == sorted(confidences, reverse=True)


# ---------------------------------------------------------------------------
# Structured JSON output
# ---------------------------------------------------------------------------

class TestStructuredOutput:
    def test_classification_result_serializable(self):
        result = classify("Patient adverse event in ward 3.")
        output = ClassificationOutput(
            categories=[
                CategoryOutput(
                    category=c.category.value,
                    confidence=c.confidence,
                    reason=c.reason,
                )
                for c in result.categories
            ]
        )
        json_str = output.model_dump_json()
        parsed = json.loads(json_str)
        assert "categories" in parsed
        assert len(parsed["categories"]) >= 1
        assert "category" in parsed["categories"][0]
        assert "confidence" in parsed["categories"][0]
        assert "reason" in parsed["categories"][0]

    def test_primary_category_property(self):
        result = classify("Adverse event: wrong medication administered.")
        output = ClassificationOutput(
            categories=[
                CategoryOutput(
                    category=c.category.value,
                    confidence=c.confidence,
                    reason=c.reason,
                )
                for c in result.categories
            ]
        )
        assert output.primary_category == "SAFETY_REPORT"
        assert output.primary_confidence > 0

    def test_category_enum_values(self):
        assert Category.SAFETY_REPORT.value == "SAFETY_REPORT"
        assert Category.QUALITY_COMPLAINT.value == "QUALITY_COMPLAINT"
        assert Category.INFO_REQUEST.value == "INFO_REQUEST"
        assert Category.NOT_RELEVANT.value == "NOT_RELEVANT"


# ---------------------------------------------------------------------------
# Rule scoring (unit-level)
# ---------------------------------------------------------------------------

class TestRuleScoring:
    def test_safety_keywords_scoring(self):
        text = "adverse event patient fall medication error"
        conf, reasons = _score_category(text.lower(), _SAFETY_KEYWORDS)
        assert conf > 0.3
        assert len(reasons) >= 2

    def test_quality_keywords_scoring(self):
        text = "complaint about rude staff and poor service"
        conf, reasons = _score_category(text.lower(), _QUALITY_KEYWORDS)
        assert conf > 0.3
        assert len(reasons) >= 2

    def test_no_keywords_zero_confidence(self):
        text = "hello world test"
        conf, reasons = _score_category(text.lower(), _SAFETY_KEYWORDS)
        assert conf == 0.0
        assert len(reasons) == 0

    def test_short_text_penalty(self):
        text = "fall"
        conf, reasons = _score_category(text.lower(), _SAFETY_KEYWORDS)
        # Should be penalised for being very short
        assert conf < 0.15

    def test_multiple_matches_boost(self):
        text = "adverse event adverse reaction side effect"
        conf, _ = _score_category(text.lower(), _SAFETY_KEYWORDS)
        # Multiple distinct matches should increase confidence
        assert conf > 0.4
