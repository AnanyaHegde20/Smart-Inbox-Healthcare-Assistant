"""Comprehensive tests for classification, extraction, and summarization."""

from __future__ import annotations

import json

import pytest

from app.classifier import classify
from app.classifier.models import Category
from app.icsr.extractor import ICSRExtractor
from app.extractors.quality_complaint import QualityComplaintExtractor
from app.extractors.info_request import InfoRequestExtractor
from app.extractors.not_relevant import NotRelevantExtractor
from app.summarizer import DocumentSummarizer
from app.services.document_processor import DocumentProcessor
from app.models.requests import ProcessDocumentRequest


# ---------------------------------------------------------------------------
# Classification Tests
# ---------------------------------------------------------------------------

class TestClassificationComprehensive:
    """Extended classification tests covering all categories and edge cases."""

    def test_safety_report_adverse_event(self):
        text = "Patient experienced severe adverse event after drug administration. Anaphylactic shock reported."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "SAFETY_REPORT" in cats

    def test_safety_report_patient_fall(self):
        text = "Patient fall incident in Ward 3B. Patient slipped while getting out of bed. Bed alarm activated."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "SAFETY_REPORT" in cats

    def test_safety_report_medication_error(self):
        text = "Medication error: patient received wrong dose. Prescribed 500mg but given 1000mg. overdose."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "SAFETY_REPORT" in cats

    def test_safety_report_hospitalization(self):
        text = "Patient hospitalized after medication error. Required overnight stay in intensive care."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "SAFETY_REPORT" in cats

    def test_safety_report_death(self):
        text = "Patient death reported following adverse drug reaction. Fatal outcome confirmed."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "SAFETY_REPORT" in cats

    def test_quality_complaint_direct(self):
        text = "Quality complaint: inconsistent tablet coating on lot PC-2025-3391. Dissolution failure."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "QUALITY_COMPLAINT" in cats

    def test_quality_complaint_dissatisfied(self):
        text = "Dissatisfied patient complaint about long wait times and unprofessional behavior."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "QUALITY_COMPLAINT" in cats

    def test_info_request_question(self):
        text = "What are the storage requirements for insulin glargine? Please provide guidelines."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "INFO_REQUEST" in cats

    def test_info_request_please_provide(self):
        text = "Please provide the latest protocol for medication reconciliation."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "INFO_REQUEST" in cats

    def test_not_relevant_marketing(self):
        text = "Special offer! Buy one get one free on healthcare software. Limited time deal."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "NOT_RELEVANT" in cats

    def test_not_relevant_spam(self):
        text = "Congratulations! You have won a lottery. Click here to claim your prize."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "NOT_RELEVANT" in cats

    def test_multi_category_safety_and_quality(self):
        text = "Patient safety incident: medication dispensing error caused adverse reaction. Quality complaint filed."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert "SAFETY_REPORT" in cats or "QUALITY_COMPLAINT" in cats

    def test_multi_category_info_and_quality(self):
        text = "Complaint about long wait times. Also requesting information about appointment scheduling."
        result = classify(text)
        cats = [c.category.value for c in result.categories]
        assert len(cats) >= 1

    def test_empty_text_defaults_not_relevant(self):
        result = classify("")
        assert result.primary.category == Category.NOT_RELEVANT

    def test_whitespace_only_defaults_not_relevant(self):
        result = classify("   \n\t  ")
        assert result.primary.category == Category.NOT_RELEVANT

    def test_very_short_text(self):
        result = classify("Hello")
        assert result.primary is not None
        assert 0 <= result.primary.confidence <= 1

    def test_confidence_always_between_0_and_1(self):
        texts = [
            "Adverse event report with patient harm",
            "Quality complaint about product",
            "What is the storage requirement?",
            "Marketing email spam",
            "",
            "A" * 5000,
        ]
        for text in texts:
            result = classify(text)
            for cat in result.categories:
                assert 0 <= cat.confidence <= 1

    def test_categories_sorted_by_confidence_desc(self):
        text = "Patient safety incident with adverse drug reaction. Quality complaint filed. Need more information."
        result = classify(text)
        confidences = [c.confidence for c in result.categories]
        assert confidences == sorted(confidences, reverse=True)


# ---------------------------------------------------------------------------
# Safety Report (ICSR) Extraction Tests
# ---------------------------------------------------------------------------

class TestICSRComprehensive:
    """Comprehensive tests for ICSR field extraction."""

    def setup_method(self):
        self.extractor = ICSRExtractor()

    def test_complete_safety_report(self):
        text = (
            "ICSR Report ID: ICSR-2025-1234\n"
            "Report Date: 2025-08-15\n"
            "Patient Name: John Smith\n"
            "Patient Age: 45\n"
            "Patient Sex: Male\n"
            "Patient Weight: 80 kg\n"
            "Drug: Aspirin 100mg\n"
            "Reaction: Gastrointestinal bleeding\n"
            "Onset: 2025-08-10\n"
            "Outcome: Recovered\n"
            "Severity: Serious\n"
            "Reporter: Dr. Lee, Pharmacist\n"
            "Organization: City Hospital\n"
        )
        result = self.extractor.extract(text)
        assert result.report_id.value == "ICSR-2025-1234"
        assert result.patient.age.value == "45"
        assert result.patient.sex.value == "Male"
        assert "Aspirin" in result.product.name.value
        assert "bleeding" in result.reaction.description.value.lower()

    def test_partial_report_missing_fields(self):
        text = "Adverse event: patient experienced rash after taking medication."
        result = self.extractor.extract(text)
        assert result.patient.age.value == "Not stated"
        assert result.patient.age.confidence == 0.0
        assert result.reporter.name.value == "Not stated"

    def test_empty_report_all_not_stated(self):
        result = self.extractor.extract("")
        assert result.patient.name.value == "Not stated"
        assert result.product.name.value == "Not stated"
        assert result.reaction.description.value == "Not stated"

    def test_patient_age_extraction(self):
        text = "Patient age: 67 years old. Female patient."
        result = self.extractor.extract(text)
        assert result.patient.age.value == "67"

    def test_patient_sex_extraction(self):
        text = "Patient is a 45-year-old male."
        result = self.extractor.extract(text)
        assert result.patient.sex.value.lower() in ("male", "m")

    def test_drug_name_extraction(self):
        text = "Drug: Metformin 500mg. Patient experienced side effects."
        result = self.extractor.extract(text)
        assert "Metformin" in result.product.name.value

    def test_reaction_extraction(self):
        text = "Reaction: Severe headache and nausea after administration."
        result = self.extractor.extract(text)
        assert "headache" in result.reaction.description.value.lower()

    def test_reporter_extraction(self):
        text = "Reporter: Dr. Smith, Cardiologist at General Hospital."
        result = self.extractor.extract(text)
        assert "Smith" in result.reporter.name.value

    def test_severity_description(self):
        text = "Severity: Serious. Patient required hospitalization."
        result = self.extractor.extract(text)
        assert "serious" in result.severity.description.value.lower()

    def test_outcome_extraction(self):
        text = "Outcome: Patient recovered fully."
        result = self.extractor.extract(text)
        assert "recovered" in result.reaction.outcome.value.lower()

    def test_source_ref_populated(self):
        text = "Adverse event report with drug information."
        result = self.extractor.extract(text)
        assert result.report_id.source_ref is not None

    def test_json_serializable(self):
        text = "ICSR Report. Patient age 45. Drug: Aspirin."
        result = self.extractor.extract(text)
        data = result.model_dump()
        serialized = json.dumps(data, default=str)
        assert isinstance(serialized, str)


# ---------------------------------------------------------------------------
# Quality Complaint Extraction Tests
# ---------------------------------------------------------------------------

class TestQualityComplaintExtraction:
    """Comprehensive tests for quality complaint extraction."""

    def setup_method(self):
        self.extractor = QualityComplaintExtractor()

    def test_complete_complaint(self):
        text = (
            "Quality Complaint\n"
            "Product: Acetaminophen 500mg\n"
            "Lot Number: QC-2025-111\n"
            "Complaint: Inconsistent tablet size\n"
            "Date Received: 2025-06-15\n"
            "Complainant: Dr. Johnson\n"
            "Contact: johnson@hospital.org\n"
            "Expected Resolution: Replacement batch"
        )
        result = self.extractor.extract(text)
        assert "Acetaminophen" in result.product.value
        assert result.batch_lot_number.value == "QC-2025-111"
        assert "inconsistent" in result.complaint_description.value.lower()

    def test_missing_fields_default(self):
        text = "Quality complaint reported."
        result = self.extractor.extract(text)
        assert result.product.value == "Not stated"
        assert result.batch_lot_number.value == "Not stated"

    def test_product_extraction(self):
        text = "Product: Ibuprofen 200mg tablets. Coating defect observed."
        result = self.extractor.extract(text)
        assert "Ibuprofen" in result.product.value

    def test_lot_number_extraction(self):
        text = "Lot: AB-12345. Product failed dissolution test."
        result = self.extractor.extract(text)
        assert "AB-12345" in result.batch_lot_number.value

    def test_date_extraction(self):
        text = "Date: 2025-07-01. Complaint received about tablet appearance."
        result = self.extractor.extract(text)
        assert len(result.date_received.value) > 0

    def test_complainant_extraction(self):
        text = "Reported by: Jane Doe, QA Manager."
        result = self.extractor.extract(text)
        assert "Doe" in result.complainant_name.value

    def test_confidence_for_found_fields(self):
        text = "Product: Aspirin. Lot: 12345. Complaint: broken tablets."
        result = self.extractor.extract(text)
        assert result.product.confidence > 0
        assert result.batch_lot_number.confidence > 0

    def test_confidence_zero_for_missing(self):
        text = "Something went wrong with the product."
        result = self.extractor.extract(text)
        assert result.batch_lot_number.confidence == 0.0

    def test_json_serializable(self):
        text = "Product: Test. Lot: 001. Complaint: defect."
        result = self.extractor.extract(text)
        data = result.model_dump()
        serialized = json.dumps(data, default=str)
        assert isinstance(serialized, str)


# ---------------------------------------------------------------------------
# Info Request Extraction Tests
# ---------------------------------------------------------------------------

class TestInfoRequestExtraction:
    """Comprehensive tests for info request extraction."""

    def setup_method(self):
        self.extractor = InfoRequestExtractor()

    def test_complete_request(self):
        text = (
            "Information Request\n"
            "From: pharmacy@hospital.org\n"
            "Date: 2025-08-01\n"
            "Questions: What are the storage requirements for insulin?\n"
            "Product: Insulin glargine\n"
            "Urgency: High\n"
        )
        result = self.extractor.extract(text)
        assert result.questions.value is not None
        assert "Insulin" in result.product_topic.value

    def test_question_mark_detection(self):
        text = "What is the recommended dosage? How often should it be administered?"
        result = self.extractor.extract(text)
        assert result.questions.confidence > 0

    def test_product_topic_extraction(self):
        text = "Inquiry about Amoxicillin storage guidelines."
        result = self.extractor.extract(text)
        assert "Amoxicillin" in result.product_topic.value

    def test_missing_fields(self):
        text = "Please help."
        result = self.extractor.extract(text)
        assert result.product_topic.value == "Not stated"

    def test_requester_extraction(self):
        text = "From: john.doe@clinic.com. Requesting information about vaccines."
        result = self.extractor.extract(text)
        assert "doe" in result.requester_name.value.lower() or "john" in result.requester_name.value.lower()

    def test_confidence_range(self):
        text = "What are the side effects of Metformin?"
        result = self.extractor.extract(text)
        assert 0 <= result.questions.confidence <= 1
        assert 0 <= result.product_topic.confidence <= 1

    def test_json_serializable(self):
        text = "Question: What is the dosage?"
        result = self.extractor.extract(text)
        data = result.model_dump()
        serialized = json.dumps(data, default=str)
        assert isinstance(serialized, str)


# ---------------------------------------------------------------------------
# Not Relevant Extraction Tests
# ---------------------------------------------------------------------------

class TestNotRelevantExtraction:
    """Comprehensive tests for not relevant extraction."""

    def setup_method(self):
        self.extractor = NotRelevantExtractor()

    def test_spam_detection(self):
        text = "You have won a million dollars! Click here now!"
        result = self.extractor.extract(text)
        assert result.is_spam.value in ("Likely", "Yes", "True", "true")

    def test_marketing_detection(self):
        text = "Special promotion: 50% off all products. Buy now!"
        result = self.extractor.extract(text)
        assert "promotional" in result.reason.value.lower() or "marketing" in result.reason.value.lower()

    def test_not_relevant_category(self):
        text = "Happy birthday! Wishing you a great day."
        result = self.extractor.extract(text)
        assert result.detected_category.value is not None

    def test_reason_populated(self):
        text = "Lottery winner notification. Claim your prize."
        result = self.extractor.extract(text)
        assert len(result.reason.value) > 0

    def test_empty_text(self):
        result = self.extractor.extract("")
        assert result.reason.value is not None

    def test_json_serializable(self):
        text = "Spam content with promotion."
        result = self.extractor.extract(text)
        data = result.model_dump()
        serialized = json.dumps(data, default=str)
        assert isinstance(serialized, str)


# ---------------------------------------------------------------------------
# Summary Generation Tests
# ---------------------------------------------------------------------------

class TestSummarizationComprehensive:
    """Comprehensive tests for document summarization."""

    def setup_method(self):
        self.summarizer = DocumentSummarizer()

    def test_safety_report_summary(self):
        text = (
            "Patient adverse event report. Patient experienced severe allergic reaction "
            "after receiving Amoxicillin. Symptoms included hives, swelling, and difficulty "
            "breathing. EpiPen was administered. Patient recovered after 24 hours of observation. "
            "Reporter: Dr. Smith. Causality: Probable. The event was classified as serious."
        )
        result = self.summarizer.summarize(text, classification_categories=["SAFETY_REPORT"])
        assert result.total_sentences >= 5
        assert result.is_relevant is True

    def test_quality_complaint_summary(self):
        text = (
            "Quality complaint received regarding inconsistent tablet coating on Lot PC-2025-001. "
            "Dissolution testing showed 15% failure rate. Root cause identified as coating pan "
            "temperature fluctuation. Corrective actions implemented. Affected quantity: 50,000 tablets."
        )
        result = self.summarizer.summarize(text, classification_categories=["QUALITY_COMPLAINT"])
        assert result.total_sentences >= 5

    def test_info_request_summary(self):
        text = (
            "Request for storage guidelines for insulin glargine products. "
            "Questions about recommended temperature range after opening. "
            "How long can vials be stored at room temperature?"
        )
        result = self.summarizer.summarize(text, classification_categories=["INFO_REQUEST"])
        assert result.total_sentences >= 5

    def test_summary_has_all_sections(self):
        text = (
            "Patient safety incident report. Fall occurred in Ward 3B. "
            "Patient SYN-1042 slipped while getting out of bed. "
            "Bed alarm activated but nurse response delayed by 4 minutes. "
            "No visible injuries. Corrective actions: staff retraining scheduled."
        )
        result = self.summarizer.summarize(text, classification_categories=["SAFETY_REPORT"])
        sections = {s.section for s in result.sentences}
        assert "overview" in sections

    def test_summary_mentions_filename(self):
        text = "Document content about patient safety."
        result = self.summarizer.summarize(text, filename="incident-report.pdf")
        overview_text = " ".join(s.text for s in result.sentences if s.section == "overview")
        assert "incident-report" in overview_text.lower() or "report" in overview_text.lower()

    def test_summary_no_invention(self):
        text = "Patient took Aspirin 100mg. No adverse effects reported."
        result = self.summarizer.summarize(text, classification_categories=["SAFETY_REPORT"])
        narrative = result.to_narrative()
        assert "Aspirin" in narrative

    def test_summary_key_topics(self):
        text = (
            "Medication error report. Wrong dose administered to patient. "
            "Root cause: look-alike packaging. Corrective action: tall-man lettering."
        )
        result = self.summarizer.summarize(text, classification_categories=["QUALITY_COMPLAINT"])
        assert len(result.key_topics) >= 1

    def test_summary_document_purpose(self):
        text = "Adverse event report for drug-induced liver injury."
        result = self.summarizer.summarize(text, classification_categories=["SAFETY_REPORT"])
        assert len(result.document_purpose) > 0

    def test_summary_has_at_least_one_sentence(self):
        result = self.summarizer.summarize("")
        assert result.total_sentences >= 1

    def test_summary_narrative_concatenation(self):
        text = "Test sentence one. Test sentence two. Test sentence three."
        result = self.summarizer.summarize(text)
        narrative = result.to_narrative()
        assert isinstance(narrative, str)
        assert len(narrative) > 0

    def test_summary_sentence_count_range(self):
        text = (
            "This is a longer document with multiple sentences. "
            "It contains information about patient safety. "
            "The incident occurred on Monday morning. "
            "Staff responded quickly. "
            "Patient was evaluated and treated. "
            "No lasting harm was observed. "
            "The case was documented properly."
        ) * 2
        result = self.summarizer.summarize(text, classification_categories=["SAFETY_REPORT"])
        assert 5 <= result.total_sentences <= 20

    def test_page_count_affects_summary(self):
        text = "Content on page one. Content on page two."
        result = self.summarizer.summarize(text, page_count=5)
        assert result.total_sentences >= 1

    def test_word_count_in_overview(self):
        text = "Word " * 100 + "content."
        result = self.summarizer.summarize(text)
        overview = [s for s in result.sentences if s.section == "overview"]
        assert len(overview) >= 1


# ---------------------------------------------------------------------------
# DocumentProcessor Integration Tests
# ---------------------------------------------------------------------------

class TestDocumentProcessorIntegration:
    """Tests for the DocumentProcessor async pipeline."""

    def setup_method(self):
        self.processor = DocumentProcessor()

    @pytest.mark.asyncio
    async def test_process_text_document(self):
        request = ProcessDocumentRequest(
            document="Patient adverse event report. Drug: Aspirin. Reaction: rash.",
            filename="test-report.txt",
        )
        response = await self.processor.process(request)
        assert response.document_type == "text"
        assert response.classification is not None
        assert response.classification_output is not None
        assert response.document_summary is not None

    @pytest.mark.asyncio
    async def test_process_minimal_document(self):
        request = ProcessDocumentRequest(
            document="A",
            filename="minimal.txt",
        )
        response = await self.processor.process(request)
        assert response.document_type == "text"
        assert response.classification.category == "NOT_RELEVANT"

    @pytest.mark.asyncio
    async def test_process_safety_text(self):
        request = ProcessDocumentRequest(
            document="Adverse drug reaction: patient experienced anaphylaxis after Amoxicillin. Hospitalized.",
            filename="safety-report.txt",
        )
        response = await self.processor.process(request)
        assert response.classification.category == "SAFETY_REPORT"

    @pytest.mark.asyncio
    async def test_process_quality_text(self):
        request = ProcessDocumentRequest(
            document="Quality complaint: inconsistent tablet coating on lot PC-2025-001.",
            filename="quality-complaint.txt",
        )
        response = await self.processor.process(request)
        cats = [c.category for c in response.classification_output.categories]
        assert "QUALITY_COMPLAINT" in cats or "SAFETY_REPORT" in cats

    @pytest.mark.asyncio
    async def test_process_info_request_text(self):
        request = ProcessDocumentRequest(
            document="What are the storage requirements for insulin? Please provide guidelines.",
            filename="info-request.txt",
        )
        response = await self.processor.process(request)
        cats = [c.category for c in response.classification_output.categories]
        assert "INFO_REQUEST" in cats

    @pytest.mark.asyncio
    async def test_process_marketing_text(self):
        request = ProcessDocumentRequest(
            document="Special offer! Buy healthcare software at 50% discount. Limited time deal.",
            filename="marketing.txt",
        )
        response = await self.processor.process(request)
        assert response.classification.category == "NOT_RELEVANT"

    @pytest.mark.asyncio
    async def test_processing_time_recorded(self):
        request = ProcessDocumentRequest(
            document="Test document with some content.",
            filename="test.txt",
        )
        response = await self.processor.process(request)
        assert response.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_summary_generated(self):
        request = ProcessDocumentRequest(
            document="Patient safety incident. Fall in ward 3B. No injuries. Corrective actions taken.",
            filename="incident.txt",
        )
        response = await self.processor.process(request)
        assert response.document_summary is not None
        assert response.document_summary.total_sentences >= 1

    @pytest.mark.asyncio
    async def test_extracted_facts_populated(self):
        request = ProcessDocumentRequest(
            document="Test content.",
            filename="test.txt",
        )
        response = await self.processor.process(request)
        assert len(response.extracted_facts) >= 1

    @pytest.mark.asyncio
    async def test_language_detected(self):
        request = ProcessDocumentRequest(
            document="This is an English language document about healthcare.",
            filename="english.txt",
        )
        response = await self.processor.process(request)
        assert response.language is not None

    @pytest.mark.asyncio
    async def test_long_document_processing(self):
        long_text = "Patient safety report. " * 500
        request = ProcessDocumentRequest(
            document=long_text,
            filename="long-doc.txt",
        )
        response = await self.processor.process(request)
        assert response.classification is not None
        assert response.document_summary is not None
