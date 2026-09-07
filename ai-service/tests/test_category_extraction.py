"""Tests proving DocumentProcessor uses category-specific extractors.

Each test sends text that triggers a specific classification,
then verifies the returned extracted_facts contain real fields
from the corresponding extractor (not the old stub).
"""

from __future__ import annotations

import pytest

from app.services.document_processor import DocumentProcessor
from app.models.requests import ProcessDocumentRequest


processor = DocumentProcessor()


# ---------------------------------------------------------------------------
# SAFETY_REPORT → ICSRExtractor
# ---------------------------------------------------------------------------

class TestSafetyReportExtraction:
    """Verify SAFETY_REPORT triggers ICSRExtractor and returns ICSR fields."""

    SAFETY_TEXT = """\
Patient adverse event report
Patient name: John Smith
Age: 45
Sex: Male
Weight: 80 kg

Product: Aspirin 100mg
Manufacturer: PharmaCorp
Lot number: LOT-2025-001
Dosage: 100mg daily
Route: oral

Reaction: Anaphylactic shock
Onset date: 2025-08-15
Outcome: Recovered
Seriousness: Yes

Severity grade: 3
Hospitalization: Yes
Life threatening: No
Death: No

Reporter name: Dr. Jane Doe
Role: Physician
Organization: City Hospital

Causality: Probable
Action taken: Drug discontinued

Report ID: SR-2025-001
Report date: 2025-08-16
Summary: Patient developed anaphylaxis 30 minutes after first dose of Aspirin.
"""

    @pytest.mark.asyncio
    async def test_safety_fields_returned(self):
        """ICSR fields like patient_age, product_name, reaction_description must appear."""
        req = ProcessDocumentRequest(
            document=self.SAFETY_TEXT,
            filename="adverse-event.txt",
        )
        resp = await processor.process(req)

        assert resp.classification.category == "SAFETY_REPORT"
        keys = {f.key for f in resp.extracted_facts}
        # Patient fields
        assert "patient_age" in keys
        assert "patient_sex" in keys
        assert "patient_name" in keys
        # Product fields
        assert "product_name" in keys
        assert "product_manufacturer" in keys
        assert "product_lot_number" in keys
        # Reaction fields
        assert "reaction_description" in keys
        assert "reaction_outcome" in keys
        # Severity fields
        assert "severity_hospitalization" in keys
        # Report fields
        assert "report_id" in keys

    @pytest.mark.asyncio
    async def test_safety_field_values_are_real(self):
        """Extracted values should match actual content, not stubs."""
        req = ProcessDocumentRequest(
            document=self.SAFETY_TEXT,
            filename="adverse-event.txt",
        )
        resp = await processor.process(req)
        by_key = {f.key: f for f in resp.extracted_facts}

        assert by_key["patient_age"].value == "45"
        assert by_key["patient_sex"].value == "Male"
        assert by_key["product_name"].value == "Aspirin 100mg"
        assert by_key["product_lot_number"].value == "LOT-2025-001"
        assert by_key["report_id"].value == "SR-2025-001"
        # Must NOT be the old stub
        assert not any(f.key == "filename" for f in resp.extracted_facts)
        assert not any(f.key == "word_count" for f in resp.extracted_facts)


# ---------------------------------------------------------------------------
# QUALITY_COMPLAINT → QualityComplaintExtractor
# ---------------------------------------------------------------------------

class TestQualityComplaintExtraction:
    """Verify QUALITY_COMPLAINT triggers QualityComplaintExtractor."""

    QUALITY_TEXT = """\
Complaint: Tablet coating inconsistency
Product: Acetaminophen 500mg Tablets
Lot number: PC-2025-3391
Complaint description: Dissolution testing shows 15% of tablets failing specification.
Complaint category: Product quality
Complainant name: Quality Department
Complainant contact: quality@pharma-cure-labs.com
Date received: 2025-08-20
Expected resolution: Investigation and replacement of affected batch
Photo: attached
"""

    @pytest.mark.asyncio
    async def test_quality_fields_returned(self):
        """Quality-specific fields must appear in extracted_facts."""
        req = ProcessDocumentRequest(
            document=self.QUALITY_TEXT,
            filename="quality-complaint.txt",
        )
        resp = await processor.process(req)

        assert resp.classification.category == "QUALITY_COMPLAINT"
        keys = {f.key for f in resp.extracted_facts}
        assert "product" in keys
        assert "batch_lot_number" in keys
        assert "complaint_description" in keys
        assert "complainant_name" in keys

    @pytest.mark.asyncio
    async def test_quality_field_values(self):
        """Values should match the actual complaint text."""
        req = ProcessDocumentRequest(
            document=self.QUALITY_TEXT,
            filename="quality-complaint.txt",
        )
        resp = await processor.process(req)
        by_key = {f.key: f for f in resp.extracted_facts}

        assert by_key["product"].value == "Acetaminophen 500mg Tablets"
        assert by_key["batch_lot_number"].value == "PC-2025-3391"
        assert "15%" in by_key["complaint_description"].value


# ---------------------------------------------------------------------------
# INFO_REQUEST → InfoRequestExtractor
# ---------------------------------------------------------------------------

class TestInfoRequestExtraction:
    """Verify INFO_REQUEST triggers InfoRequestExtractor."""

    INFO_TEXT = """\
Information request
Subject: Insulin storage requirements
Product: Insulin glargine

What is the recommended temperature range after opening?
How long can vials be stored at room temperature?
Is stability data available for opened vials?

Requester name: Pharmacy Department
Contact: pharmacy@riverside-medical.org
Urgency: medium
Preferred response format: email
"""

    @pytest.mark.asyncio
    async def test_info_fields_returned(self):
        """Info-request fields like questions, product_topic must appear."""
        req = ProcessDocumentRequest(
            document=self.INFO_TEXT,
            filename="storage-inquiry.txt",
        )
        resp = await processor.process(req)

        assert resp.classification.category == "INFO_REQUEST"
        keys = {f.key for f in resp.extracted_facts}
        assert "questions" in keys
        assert "product_topic" in keys
        assert "requester_name" in keys

    @pytest.mark.asyncio
    async def test_info_field_values(self):
        """Values should match the actual inquiry text."""
        req = ProcessDocumentRequest(
            document=self.INFO_TEXT,
            filename="storage-inquiry.txt",
        )
        resp = await processor.process(req)
        by_key = {f.key: f for f in resp.extracted_facts}

        assert "insulin" in by_key["product_topic"].value.lower()
        assert by_key["requester_name"].value == "Pharmacy Department"


# ---------------------------------------------------------------------------
# NOT_RELEVANT → NotRelevantExtractor
# ---------------------------------------------------------------------------

class TestNotRelevantExtraction:
    """Verify NOT_RELEVANT triggers NotRelevantExtractor."""

    SPAM_TEXT = """\
Buy our revolutionary AI healthcare platform!
Limited time offer: 40% off annual subscriptions.
Schedule a demo today and receive a free consultation.
Click here to claim your discount.
Congratulations! You have been selected for a special offer.
"""

    @pytest.mark.asyncio
    async def test_not_relevant_fields_returned(self):
        """Not-relevant fields like is_spam, detected_category must appear."""
        req = ProcessDocumentRequest(
            document=self.SPAM_TEXT,
            filename="marketing.txt",
        )
        resp = await processor.process(req)

        assert resp.classification.category == "NOT_RELEVANT"
        keys = {f.key for f in resp.extracted_facts}
        assert "is_spam" in keys
        assert "detected_category" in keys

    @pytest.mark.asyncio
    async def test_not_relevant_spam_detected(self):
        """Marketing email should be flagged as spam."""
        req = ProcessDocumentRequest(
            document=self.SPAM_TEXT,
            filename="marketing.txt",
        )
        resp = await processor.process(req)
        by_key = {f.key: f for f in resp.extracted_facts}

        assert by_key["is_spam"].value in ("Yes", "Likely")


# ---------------------------------------------------------------------------
# No old stub remnants
# ---------------------------------------------------------------------------

class TestNoStubFacts:
    """Ensure the old filename/word_count stub is never returned."""

    @pytest.mark.asyncio
    async def test_no_filename_stub(self):
        req = ProcessDocumentRequest(
            document="Patient adverse event: anaphylactic shock after medication.",
            filename="test.txt",
        )
        resp = await processor.process(req)
        keys = {f.key for f in resp.extracted_facts}
        assert "filename" not in keys
        assert "word_count" not in keys

    @pytest.mark.asyncio
    async def test_minimal_text_still_extracts(self):
        """Very short text should still use extractors, not stub."""
        req = ProcessDocumentRequest(
            document="Complaint about defective product. Lot number ABC-123.",
            filename="complaint.txt",
        )
        resp = await processor.process(req)
        keys = {f.key for f in resp.extracted_facts}
        # Should have real extraction fields, not stub
        assert "filename" not in keys
        assert "word_count" not in keys
