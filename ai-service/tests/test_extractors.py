"""Tests for QUALITY_COMPLAINT, INFO_REQUEST, and NOT_RELEVANT extractors.

All test data is synthetic.  No real patient information is used.
"""

from __future__ import annotations

import json

import pytest

from app.extractors import (
    QualityComplaintExtractor,
    InfoRequestExtractor,
    NotRelevantExtractor,
)


# ---------------------------------------------------------------------------
# Synthetic documents
# ---------------------------------------------------------------------------

QUALITY_COMPLETE = """
Complaint ID: QC-2025-0123
Date Received: 2025-04-01

Complainant: Test Customer X
Contact: test.customer@example.com

Product: TestMed 250mg Tablets
Lot Number: TM-LOT-9999

Complaint Type: Product Quality

Complaint Description: The tablets arrived with visible discoloration and an unusual smell. Packaging was intact but the tablets inside appear degraded. I have been using this product for months and this is the first time I see this issue.

Photo: Included

Expected Resolution: Replacement and investigation into batch quality
"""

QUALITY_MINIMAL = """
I have a problem with my medication. It doesn't look right.
"""

QUALITY_NO_PHOTO = """
Product: TestDevice XL
Complaint: Device makes unusual noise during operation.
Photo: None
"""

INFO_REQUEST_COMPLETE = """
From: Test Requester Y
Contact: requester@hospital.org
Subject: Drug Interaction Query

Please tell me: What are the known drug interactions between TestDrug A and TestDrug B?
Can you also provide the latest clinical guidelines for dosing in renal impairment?
Date: 2025-03-20
Urgency: High
Preferred Format: Written
"""

INFO_REQUEST_MINIMAL = """
What are the side effects of Aspirin?
"""

NOT_RELEVANT_SPAM = """
Dear Friend,

Congratulations! You have been selected as our lucky winner!
Click here to claim your free gift. Limited time offer.
Buy now and get 50% discount on all medications.
Unsubscribe from this list.
"""

NOT_RELEVANT_NEWSLETTER = """
Weekly Health Digest

Subscribe to our newsletter for the latest health tips and promotions.
Opt out at any time.
"""

NOT_RELEVANT_OUT_OF_OFFICE = """
Out of Office auto-reply: I am currently unavailable and will return on Monday.
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def qc_extractor() -> QualityComplaintExtractor:
    return QualityComplaintExtractor()


@pytest.fixture()
def ir_extractor() -> InfoRequestExtractor:
    return InfoRequestExtractor()


@pytest.fixture()
def nr_extractor() -> NotRelevantExtractor:
    return NotRelevantExtractor()


# ---------------------------------------------------------------------------
# QUALITY_COMPLAINT tests
# ---------------------------------------------------------------------------

class TestQualityComplaintComplete:
    def test_product(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf")
        assert "TestMed" in result.product.value
        assert result.product.confidence >= 0.7

    def test_lot_number(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf")
        assert "TM-LOT-9999" in result.batch_lot_number.value
        assert result.batch_lot_number.confidence >= 0.8

    def test_description(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf")
        assert "discoloration" in result.complaint_description.value.lower()
        assert result.complaint_description.confidence >= 0.7

    def test_photo_mentioned(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf")
        assert result.photo_mentioned.value == "Yes"
        assert result.photo_mentioned.confidence >= 0.7

    def test_complaint_category(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf")
        assert "product quality" in result.complaint_category.value.lower()

    def test_complainant_name(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf")
        assert "Test Customer" in result.complainant_name.value

    def test_complainant_contact(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf")
        assert "@" in result.complainant_contact.value

    def test_date_received(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf")
        assert "2025" in result.date_received.value

    def test_expected_resolution(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf")
        assert "replacement" in result.expected_resolution.value.lower()


class TestQualityComplaintNoPhoto:
    def test_photo_not_present(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_NO_PHOTO, filename="complaint.txt")
        assert result.photo_mentioned.value == "No"
        assert result.photo_mentioned.confidence >= 0.7


class TestQualityComplaintMinimal:
    def test_product_may_be_inferred(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_MINIMAL, filename="minimal.txt")
        # "problem with my medication" legitimately mentions a product
        assert result.product.value != ""

    def test_missing_structured_fields_not_stated(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_MINIMAL, filename="minimal.txt")
        assert result.batch_lot_number.value == "Not stated"
        assert result.complainant_name.value == "Not stated"
        assert result.complainant_contact.value == "Not stated"
        assert result.date_received.value == "Not stated"
        assert result.expected_resolution.value == "Not stated"

    def test_description_extracted(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_MINIMAL, filename="minimal.txt")
        assert result.complaint_description.value != ""

    def test_not_stated_confidence_zero(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_MINIMAL, filename="minimal.txt")
        assert result.batch_lot_number.confidence == 0.0
        assert result.complainant_name.confidence == 0.0


class TestQualityComplaintSourceRef:
    def test_pdf_source(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf")
        assert result.product.source_ref.document_type == "pdf"
        assert result.product.source_ref.filename == "complaint.pdf"

    def test_email_source(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.eml")
        assert result.product.source_ref.document_type == "email"

    def test_page_preserved(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf", page=2)
        assert result.product.source_ref.page == 2


class TestQualityComplaintJSON:
    def test_serializable(self, qc_extractor: QualityComplaintExtractor):
        result = qc_extractor.extract(QUALITY_COMPLETE, filename="complaint.pdf")
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        assert "product" in parsed
        assert "batch_lot_number" in parsed
        assert "complaint_description" in parsed
        assert "photo_mentioned" in parsed
        assert "source_ref" in parsed["product"]


# ---------------------------------------------------------------------------
# INFO_REQUEST tests
# ---------------------------------------------------------------------------

class TestInfoRequestComplete:
    def test_questions(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_COMPLETE, filename="inquiry.eml")
        assert "?" in result.questions.value
        assert result.questions.confidence >= 0.6

    def test_product_topic(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_COMPLETE, filename="inquiry.eml")
        assert "drug interaction" in result.product_topic.value.lower() or "TestDrug" in result.product_topic.value

    def test_urgency(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_COMPLETE, filename="inquiry.eml")
        assert "high" in result.urgency.value.lower()

    def test_requester_name(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_COMPLETE, filename="inquiry.eml")
        assert "Test Requester" in result.requester_name.value

    def test_requester_contact(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_COMPLETE, filename="inquiry.eml")
        assert "@" in result.requester_contact.value

    def test_date_submitted(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_COMPLETE, filename="inquiry.eml")
        assert "2025" in result.date_submitted.value

    def test_preferred_format(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_COMPLETE, filename="inquiry.eml")
        assert "written" in result.preferred_response_format.value.lower()


class TestInfoRequestMinimal:
    def test_questions_extracted(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_MINIMAL, filename="minimal.txt")
        assert "?" in result.questions.value

    def test_missing_fields_not_stated(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_MINIMAL, filename="minimal.txt")
        assert result.requester_name.value == "Not stated"
        assert result.requester_contact.value == "Not stated"
        assert result.date_submitted.value == "Not stated"
        assert result.preferred_response_format.value == "Not stated"


class TestInfoRequestSourceRef:
    def test_source_ref(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_COMPLETE, filename="inquiry.eml")
        assert result.questions.source_ref.document_type == "email"

    def test_page_preserved(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_COMPLETE, filename="inquiry.pdf", page=1)
        assert result.questions.source_ref.page == 1


class TestInfoRequestJSON:
    def test_serializable(self, ir_extractor: InfoRequestExtractor):
        result = ir_extractor.extract(INFO_REQUEST_COMPLETE, filename="inquiry.eml")
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        assert "questions" in parsed
        assert "product_topic" in parsed
        assert "source_ref" in parsed["questions"]


# ---------------------------------------------------------------------------
# NOT_RELEVANT tests
# ---------------------------------------------------------------------------

class TestNotRelevantSpam:
    def test_is_spam(self, nr_extractor: NotRelevantExtractor):
        result = nr_extractor.extract(NOT_RELEVANT_SPAM, filename="spam.eml")
        assert result.is_spam.value in ("Yes", "Likely")
        assert result.is_spam.confidence > 0.5

    def test_detected_category(self, nr_extractor: NotRelevantExtractor):
        result = nr_extractor.extract(NOT_RELEVANT_SPAM, filename="spam.eml")
        # Either a label was extracted or the field defaults to Not stated
        assert result.detected_category.value != "" or result.detected_category.value == "Not stated"

    def test_reason_populated(self, nr_extractor: NotRelevantExtractor):
        result = nr_extractor.extract(NOT_RELEVANT_SPAM, filename="spam.eml")
        assert result.reason.value != "Not stated"
        assert result.reason.confidence > 0.4


class TestNotRelevantNewsletter:
    def test_reason_contains_marketing(self, nr_extractor: NotRelevantExtractor):
        result = nr_extractor.extract(NOT_RELEVANT_NEWSLETTER, filename="newsletter.txt")
        assert "marketing" in result.reason.value.lower() or "newsletter" in result.reason.value.lower()


class TestNotRelevantOutOfOffice:
    def test_reason_contains_auto(self, nr_extractor: NotRelevantExtractor):
        result = nr_extractor.extract(NOT_RELEVANT_OUT_OF_OFFICE, filename="ooo.eml")
        assert "auto" in result.reason.value.lower() or "automated" in result.reason.value.lower()


class TestNotRelevantMissing:
    def test_empty_text(self, nr_extractor: NotRelevantExtractor):
        result = nr_extractor.extract("", filename="empty.txt")
        assert result.reason.value != ""
        assert result.is_spam.value == "Not stated"

    def test_generic_fallback_reason(self, nr_extractor: NotRelevantExtractor):
        result = nr_extractor.extract("Just some random text about nothing.", filename="random.txt")
        assert result.reason.value != "Not stated"
        assert result.reason.confidence > 0.3


class TestNotRelevantSourceRef:
    def test_source_ref(self, nr_extractor: NotRelevantExtractor):
        result = nr_extractor.extract(NOT_RELEVANT_SPAM, filename="spam.eml")
        assert result.reason.source_ref.document_type == "email"

    def test_page_preserved(self, nr_extractor: NotRelevantExtractor):
        result = nr_extractor.extract(NOT_RELEVANT_SPAM, filename="spam.pdf", page=3)
        assert result.reason.source_ref.page == 3


class TestNotRelevantJSON:
    def test_serializable(self, nr_extractor: NotRelevantExtractor):
        result = nr_extractor.extract(NOT_RELEVANT_SPAM, filename="spam.eml")
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        assert "reason" in parsed
        assert "is_spam" in parsed
        assert "detected_category" in parsed
        assert "source_ref" in parsed["reason"]
