"""Tests for document summarization.

All test data is synthetic. No real patient information is used.
"""

from __future__ import annotations

import pytest

from app.summarizer import DocumentSummarizer, DocumentSummary, SummarySentence


# ---------------------------------------------------------------------------
# Synthetic test documents
# ---------------------------------------------------------------------------

SAFETY_REPORT_TEXT = """
ADVERSE EVENT REPORT - CONFIDENTIAL

Report ID: AER-2025-0198
Date of Report: 2025-06-15
Reporting Facility: Test General Hospital

Patient Information:
Patient Name: Test Subject Alpha
Date of Birth: 03/22/1965
Age: 60 years
Sex: Male

Event Description:
On 06/10/2025 at approximately 14:30, the patient experienced an unexpected
fall in Room 302 of the medical surgical unit. The patient was found on the
floor by nurse Test Nurse Beta. No injuries were observed at the time of
assessment. The patient's vital signs were monitored and remained stable.

Product Involved:
Medication: Metformin 500mg
Lot Number: MFG-2025-0112
Manufacturer: Test Pharma Inc.

Actions Taken:
The fall was reported to the attending physician, Dr. Test Physician Gamma.
A post-fall assessment was completed. The patient's medication list was
reviewed for potential contributing factors. No changes to medication were
made at this time.

Outcome: Recovered without injury

Reported by: Test Nurse Beta, RN
Contact: test.nurse@hospital.org
"""

QUALITY_COMPLAINT_TEXT = """
CUSTOMER COMPLAINT FORM

Complaint ID: QC-2025-0312
Date Received: 2025-07-20

Complainant Information:
Name: Test Complainant Delta
Phone: 555-012-3456
Email: complainant@test.com

Complaint Details:
Product: Blood Pressure Monitor Model BPM-200
Lot Number: BPM-LOT-2025-088

Description of Complaint:
The blood pressure monitor purchased on 07/15/2025 has been giving
inconsistent readings. When compared with the hospital grade monitor,
the readings differ by 15-20 mmHg. The device was used according to
the instructions provided. This poses a potential patient safety risk.

Category: Device malfunction
Severity: Moderate

Resolution Requested:
The complainant is requesting a replacement device and assurance that
the product has been tested for accuracy.

Photo Attached: No

Status: Under investigation
"""

INFO_REQUEST_TEXT = """
EMAIL - INFORMATION REQUEST

From: Test Requester Epsilon
Date: 2025-08-01
Subject: Question about medication storage requirements

Dear Medical Records Department,

I am writing to inquire about the storage requirements for the
following medications:

1. What is the proper storage temperature for Insulin Glargine?
2. Can the medication be stored after opening?
3. What is the maximum duration after first use?

This information is needed for our pharmacy inventory management
system. Please respond at your earliest convenience.

Thank you,
Test Requester Epsilon
Contact: requester@test.org
"""

NOT_RELEVANT_TEXT = """
SUBJECT: You've Won a FREE Vacation!

Congratulations! You have been selected as the winner of our
exclusive vacation giveaway. Click here to claim your free trip
to the Caribbean.

This offer expires in 24 hours. Act now!

To unsubscribe, click here.
"""

MINIMAL_TEXT = "Short document with minimal content."

EMPTY_TEXT = ""

LONG_TEXT = """
This is a comprehensive medical document containing detailed patient information.
The patient Test Subject Zeta was admitted to Test Hospital on 01/15/2025.
Diagnosis: Acute myocardial infarction.
Treatment: Cardiac catheterization with stent placement.
The procedure was performed by Dr. Test Physician Eta.
Post-procedure, the patient was monitored in the cardiac care unit.
Vital signs remained stable throughout the recovery period.
The patient was discharged on 01/22/2025 with follow-up instructions.
Medications prescribed at discharge included Aspirin 81mg daily,
Clopidogrel 75mg daily, and Atorvastatin 40mg daily.
The patient was advised to follow a cardiac rehabilitation program.
A follow-up appointment was scheduled for 02/05/2025.
The total length of stay was 7 days.
No complications were reported during the hospitalization.
""" * 5  # Repeat to ensure sufficient content


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSummarySentence:
    """Tests for SummarySentence model."""

    def test_create_sentence(self):
        s = SummarySentence(index=1, text="Test sentence.", section="overview")
        assert s.index == 1
        assert s.text == "Test sentence."
        assert s.section == "overview"
        assert s.source_ref is None

    def test_sentence_with_source_ref(self):
        ref = {"page": 1, "section": "Patient Info"}
        s = SummarySentence(index=2, text="Has source.", section="case_info", source_ref=ref)
        assert s.source_ref == ref

    def test_sentence_section_values(self):
        valid_sections = ["overview", "case_info", "missing_info", "relevance", "reasoning"]
        for sec in valid_sections:
            s = SummarySentence(index=1, text="Test.", section=sec)
            assert s.section == sec


class TestDocumentSummary:
    """Tests for DocumentSummary model."""

    def test_create_summary(self):
        sentences = [
            SummarySentence(index=1, text="First.", section="overview"),
            SummarySentence(index=2, text="Second.", section="case_info"),
        ]
        summary = DocumentSummary(
            sentences=sentences,
            total_sentences=2,
            is_relevant=True,
            relevance_confidence=0.85,
            key_topics=["patient safety"],
            document_purpose="Safety report",
        )
        assert summary.total_sentences == 2
        assert summary.is_relevant is True

    def test_properties_filter_by_section(self):
        sentences = [
            SummarySentence(index=1, text="Overview.", section="overview"),
            SummarySentence(index=2, text="Case.", section="case_info"),
            SummarySentence(index=3, text="Missing.", section="missing_info"),
            SummarySentence(index=4, text="Relevant.", section="relevance"),
            SummarySentence(index=5, text="Reason.", section="reasoning"),
        ]
        summary = DocumentSummary(
            sentences=sentences,
            total_sentences=5,
            is_relevant=True,
            relevance_confidence=0.7,
            key_topics=[],
            document_purpose="Test",
        )
        assert len(summary.overview_sentences) == 1
        assert len(summary.case_info_sentences) == 1
        assert len(summary.missing_info_sentences) == 1
        assert len(summary.relevance_sentences) == 1
        assert len(summary.reasoning_sentences) == 1

    def test_to_narrative(self):
        sentences = [
            SummarySentence(index=1, text="First sentence.", section="overview"),
            SummarySentence(index=2, text="Second sentence.", section="case_info"),
        ]
        summary = DocumentSummary(
            sentences=sentences,
            total_sentences=2,
            is_relevant=True,
            relevance_confidence=0.8,
            key_topics=[],
            document_purpose="Test",
        )
        narrative = summary.to_narrative()
        assert "First sentence." in narrative
        assert "Second sentence." in narrative


class TestDocumentSummarizer:
    """Tests for DocumentSummarizer."""

    def setup_method(self):
        self.summarizer = DocumentSummarizer()

    def test_empty_text_returns_empty_summary(self):
        result = self.summarizer.summarize(EMPTY_TEXT)
        assert result.total_sentences == 1
        assert result.is_relevant is False
        assert result.relevance_confidence == 0.1
        assert "empty" in result.sentences[0].text.lower()

    def test_minimal_text_returns_summary(self):
        result = self.summarizer.summarize(MINIMAL_TEXT, filename="test.txt")
        assert result.total_sentences >= 1
        assert "test.txt" in result.sentences[0].text

    def test_summary_has_10_to_15_sentences(self):
        result = self.summarizer.summarize(SAFETY_REPORT_TEXT, filename="safety.pdf")
        assert 10 <= result.total_sentences <= 15, (
            f"Expected 10-15 sentences, got {result.total_sentences}"
        )

    def test_safety_report_is_relevant(self):
        result = self.summarizer.summarize(
            SAFETY_REPORT_TEXT,
            filename="aer.pdf",
            classification_categories=["SAFETY_REPORT"],
        )
        assert result.is_relevant is True
        assert result.relevance_confidence > 0.5

    def test_not_relevant_document(self):
        result = self.summarizer.summarize(
            NOT_RELEVANT_TEXT,
            filename="spam.txt",
            classification_categories=["NOT_RELEVANT"],
        )
        assert result.is_relevant is False

    def test_summary_has_all_sections(self):
        result = self.summarizer.summarize(SAFETY_REPORT_TEXT)
        sections = {s.section for s in result.sentences}
        assert "overview" in sections
        assert "case_info" in sections
        assert "missing_info" in sections
        assert "relevance" in sections
        assert "reasoning" in sections

    def test_overview_mentions_filename(self):
        result = self.summarizer.summarize(
            SAFETY_REPORT_TEXT, filename="my_report.pdf"
        )
        overview = result.overview_sentences
        assert len(overview) >= 1
        assert "my_report.pdf" in overview[0].text

    def test_case_info_identifies_entities(self):
        result = self.summarizer.summarize(SAFETY_REPORT_TEXT)
        case_sentences = result.case_info_sentences
        assert len(case_sentences) >= 1
        combined = " ".join(s.text for s in case_sentences)
        # Should identify patient, medication, or dates
        assert any(
            keyword in combined.lower()
            for keyword in ["patient", "medication", "date", "report"]
        )

    def test_missing_info_identifies_gaps(self):
        result = self.summarizer.summarize(SAFETY_REPORT_TEXT)
        missing = result.missing_info_sentences
        assert len(missing) >= 1

    def test_relevance_section_present(self):
        result = self.summarizer.summarize(SAFETY_REPORT_TEXT)
        rel = result.relevance_sentences
        assert len(rel) >= 1
        assert "relevant" in rel[0].text.lower() or "not" in rel[0].text.lower()

    def test_key_topics_detected(self):
        result = self.summarizer.summarize(SAFETY_REPORT_TEXT)
        assert len(result.key_topics) > 0

    def test_document_purpose_not_empty(self):
        result = self.summarizer.summarize(SAFETY_REPORT_TEXT)
        assert len(result.document_purpose) > 0

    def test_narrative_concatenates_sentences(self):
        result = self.summarizer.summarize(SAFETY_REPORT_TEXT)
        narrative = result.to_narrative()
        assert len(narrative) > 100
        for sentence in result.sentences:
            assert sentence.text in narrative

    def test_quality_complaint_summary(self):
        result = self.summarizer.summarize(
            QUALITY_COMPLAINT_TEXT,
            filename="complaint.pdf",
            classification_categories=["QUALITY_COMPLAINT"],
        )
        assert result.is_relevant is True
        combined = result.to_narrative().lower()
        assert "complaint" in combined or "quality" in combined

    def test_info_request_summary(self):
        result = self.summarizer.summarize(
            INFO_REQUEST_TEXT,
            filename="request.eml",
            classification_categories=["INFO_REQUEST"],
        )
        assert result.is_relevant is True

    def test_long_text_summary(self):
        result = self.summarizer.summarize(LONG_TEXT, filename="long.pdf")
        assert 10 <= result.total_sentences <= 15

    def test_no_invention_in_summary(self):
        """Verify the summary only references content present in the source."""
        result = self.summarizer.summarize(MINIMAL_TEXT)
        narrative = result.to_narrative().lower()
        # Should not invent specific medical terms not in source
        assert "chemotherapy" not in narrative
        assert "surgery" not in narrative
        assert "diagnosis" not in narrative

    def test_source_ref_optional(self):
        result = self.summarizer.summarize(SAFETY_REPORT_TEXT)
        # Some sentences may have source_ref, some may not
        for s in result.sentences:
            assert s.source_ref is None or isinstance(s.source_ref, dict)

    def test_page_count_used(self):
        result = self.summarizer.summarize(
            SAFETY_REPORT_TEXT, page_count=5
        )
        overview = result.overview_sentences
        combined = " ".join(s.text for s in overview)
        assert "5 pages" in combined

    def test_word_count_in_overview(self):
        result = self.summarizer.summarize(SAFETY_REPORT_TEXT)
        overview = result.overview_sentences
        combined = " ".join(s.text for s in overview)
        assert "words" in combined.lower()

    def test_sentences_are_indexed_sequentially(self):
        result = self.summarizer.summarize(SAFETY_REPORT_TEXT)
        for i, s in enumerate(result.sentences, start=1):
            assert s.index == i
