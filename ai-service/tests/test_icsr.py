"""Tests for ICSR (Individual Case Safety Report) extraction.

All test data is synthetic.  No real patient information is used.

Three scenarios:
1. Complete report   – all fields present
2. Partial report    – some fields missing
3. Missing info      – most fields absent, system must return "Not stated"
"""

from __future__ import annotations

import json

import pytest

from app.icsr import ICSRExtractor, ICSRReport, FieldValue, SourceRef


# ---------------------------------------------------------------------------
# Synthetic test documents
# ---------------------------------------------------------------------------

COMPLETE_REPORT = """
Report ID: SR-2025-0042
Report Date: 2025-03-15
Report Type: Initial report

Patient Name: Test Patient A
Age: 52
Sex: Female
Weight: 68 kg
Height: 165 cm
Medical History: Hypertension, Type 2 diabetes mellitus

Reporter Name: Dr. Test Physician
Role: Physician
Organization: Test Hospital General
Contact: test.physician@hospital.org

Product: TestDrug 500mg Tablets
Manufacturer: PharmaCorp Inc.
Lot Number: PC-2025-0099
Expiry Date: 2026-12-31
Dosage: 500 mg twice daily
Route: Oral
Indication: Bacterial infection

Reaction Description: Patient developed widespread urticaria and angioedema within 2 hours of the second dose.
Onset Date: 2025-03-10
Outcome: Recovered
Seriousness: Hospitalization required

Severity Grade: 3
Severity Description: Severe allergic reaction requiring emergency treatment
Hospitalization: Yes
Life Threatening: No
Death: No
Disability: No
Congenital Anomaly: No
Other Significant: Yes

Summary: 52-year-old female developed severe allergic reaction to TestDrug. Symptoms resolved after treatment with antihistamines and corticosteroids.
Causality Assessment: Probable
Action Taken: Drug withdrawn, concomitant medication given
Additional Information: Patient has no prior history of allergic reactions to similar drugs.
"""

PARTIAL_REPORT = """
Report ID: SR-2025-0099

Patient Name: Test Subject B
Age: 34
Sex: Male

Product: PainRelief 200mg
Route: Oral

Reaction Description: Mild headache after taking medication.
Outcome: Recovered

Seriousness: Not serious
"""

MINIMAL_REPORT = """
I received a complaint about something going wrong with a medication.
Not much detail was provided in this message.
"""

EMPTY_REPORT = ""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def extractor() -> ICSRExtractor:
    return ICSRExtractor()


# ---------------------------------------------------------------------------
# Tests: Complete report extraction
# ---------------------------------------------------------------------------

class TestCompleteReport:
    def test_report_id(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert report.report_id.value == "SR-2025-0042"
        assert report.report_id.confidence >= 0.8

    def test_report_date(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "2025" in report.report_date.value

    def test_patient_name(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "Test Patient A" in report.patient.name.value
        assert report.patient.name.confidence >= 0.7

    def test_patient_age(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert report.patient.age.value == "52"
        assert report.patient.age.confidence >= 0.8

    def test_patient_sex(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "female" in report.patient.sex.value.lower()
        assert report.patient.sex.confidence >= 0.7

    def test_patient_weight(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "68" in report.patient.weight.value
        assert report.patient.weight.confidence >= 0.7

    def test_patient_height(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "165" in report.patient.height.value

    def test_patient_medical_history(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "hypertension" in report.patient.medical_history.value.lower()

    def test_reporter_name(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "Test Physician" in report.reporter.name.value

    def test_reporter_role(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "physician" in report.reporter.role.value.lower()

    def test_reporter_organization(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "Test Hospital" in report.reporter.organization.value

    def test_reporter_contact(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "@" in report.reporter.contact.value

    def test_product_name(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "TestDrug" in report.product.name.value

    def test_product_manufacturer(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "PharmaCorp" in report.product.manufacturer.value

    def test_product_lot(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "PC-2025-0099" in report.product.lot_number.value

    def test_product_dosage(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "500" in report.product.dosage.value

    def test_product_route(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "oral" in report.product.route.value.lower()

    def test_reaction_description(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "urticaria" in report.reaction.description.value.lower()

    def test_reaction_onset(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "2025" in report.reaction.onset_date.value

    def test_reaction_outcome(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "recovered" in report.reaction.outcome.value.lower()

    def test_severity_grade(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert report.severity.grade.value == "3"

    def test_severity_hospitalization(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert report.severity.hospitalization.value == "Yes"

    def test_severity_death(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert report.severity.death.value == "No"

    def test_narrative_summary(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "52-year-old" in report.narrative.summary.value

    def test_narrative_causality(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "probable" in report.narrative.causality_assessment.value.lower()

    def test_narrative_action(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert "withdrawn" in report.narrative.action_taken.value.lower()


# ---------------------------------------------------------------------------
# Tests: Partial report extraction
# ---------------------------------------------------------------------------

class TestPartialReport:
    def test_available_fields_extracted(self, extractor: ICSRExtractor):
        report = extractor.extract(PARTIAL_REPORT, filename="partial.pdf")
        assert report.report_id.value == "SR-2025-0099"
        assert report.patient.name.value == "Test Subject B"
        assert report.patient.age.value == "34"
        assert "male" in report.patient.sex.value.lower()
        assert "PainRelief" in report.product.name.value
        assert "oral" in report.product.route.value.lower()

    def test_missing_fields_are_not_stated(self, extractor: ICSRExtractor):
        report = extractor.extract(PARTIAL_REPORT, filename="partial.pdf")
        assert report.patient.weight.value == "Not stated"
        assert report.patient.height.value == "Not stated"
        assert report.patient.medical_history.value == "Not stated"
        assert report.reporter.name.value == "Not stated"
        assert report.reporter.organization.value == "Not stated"
        assert report.product.manufacturer.value == "Not stated"
        assert report.product.lot_number.value == "Not stated"

    def test_missing_fields_have_zero_confidence(self, extractor: ICSRExtractor):
        report = extractor.extract(PARTIAL_REPORT, filename="partial.pdf")
        assert report.patient.weight.confidence == 0.0
        assert report.reporter.name.confidence == 0.0
        assert report.product.manufacturer.confidence == 0.0

    def test_partial_reaction_extracted(self, extractor: ICSRExtractor):
        report = extractor.extract(PARTIAL_REPORT, filename="partial.pdf")
        assert "headache" in report.reaction.description.value.lower()
        assert "recovered" in report.reaction.outcome.value.lower()


# ---------------------------------------------------------------------------
# Tests: Missing information
# ---------------------------------------------------------------------------

class TestMissingInformation:
    def test_minimal_report_mostly_not_stated(self, extractor: ICSRExtractor):
        report = extractor.extract(MINIMAL_REPORT, filename="minimal.txt")
        # Patient fields should all be "Not stated"
        assert report.patient.name.value == "Not stated"
        assert report.patient.age.value == "Not stated"
        assert report.patient.sex.value == "Not stated"
        assert report.patient.weight.value == "Not stated"
        assert report.patient.height.value == "Not stated"
        assert report.patient.medical_history.value == "Not stated"

    def test_reporter_not_stated(self, extractor: ICSRExtractor):
        report = extractor.extract(MINIMAL_REPORT, filename="minimal.txt")
        assert report.reporter.name.value == "Not stated"
        assert report.reporter.role.value == "Not stated"
        assert report.reporter.organization.value == "Not stated"

    def test_product_not_stated(self, extractor: ICSRExtractor):
        report = extractor.extract(MINIMAL_REPORT, filename="minimal.txt")
        assert report.product.name.value == "Not stated"
        assert report.product.manufacturer.value == "Not stated"
        assert report.product.dosage.value == "Not stated"

    def test_reaction_not_stated(self, extractor: ICSRExtractor):
        report = extractor.extract(MINIMAL_REPORT, filename="minimal.txt")
        assert report.reaction.description.value == "Not stated"

    def test_severity_not_stated(self, extractor: ICSRExtractor):
        report = extractor.extract(MINIMAL_REPORT, filename="minimal.txt")
        assert report.severity.grade.value == "Not stated"
        assert report.severity.hospitalization.value == "Not stated"
        assert report.severity.death.value == "Not stated"

    def test_empty_report(self, extractor: ICSRExtractor):
        report = extractor.extract(EMPTY_REPORT, filename="empty.txt")
        assert report.patient.name.value == "Not stated"
        assert report.patient.age.value == "Not stated"
        assert report.report_id.value == "Not stated"
        assert report.product.name.value == "Not stated"

    def test_no_confidence_in_not_stated_fields(self, extractor: ICSRExtractor):
        report = extractor.extract(MINIMAL_REPORT, filename="minimal.txt")
        for field_value in [
            report.patient.name,
            report.patient.age,
            report.patient.sex,
            report.reporter.name,
            report.product.name,
            report.reaction.description,
        ]:
            assert field_value.confidence == 0.0
            assert field_value.value == "Not stated"


# ---------------------------------------------------------------------------
# Tests: Source reference tracking
# ---------------------------------------------------------------------------

class TestSourceReference:
    def test_pdf_source_ref(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        assert report.patient.name.source_ref.document_type == "pdf"
        assert report.patient.name.source_ref.filename == "report.pdf"

    def test_email_source_ref(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.eml")
        assert report.patient.name.source_ref.document_type == "email"

    def test_page_number_preserved(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf", page=3)
        assert report.patient.name.source_ref.page == 3
        assert report.product.name.source_ref.page == 3

    def test_text_source_ref(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="unknown.txt")
        assert report.patient.name.source_ref.document_type == "text"

    def test_not_stated_has_source_ref(self, extractor: ICSRExtractor):
        report = extractor.extract(MINIMAL_REPORT, filename="minimal.txt")
        assert report.patient.name.source_ref.document_type == "text"


# ---------------------------------------------------------------------------
# Tests: Structured JSON output
# ---------------------------------------------------------------------------

class TestStructuredJSONOutput:
    def test_report_serializable(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        json_str = report.model_dump_json()
        parsed = json.loads(json_str)
        assert "patient" in parsed
        assert "reporter" in parsed
        assert "product" in parsed
        assert "reaction" in parsed
        assert "severity" in parsed
        assert "narrative" in parsed

    def test_field_value_structure(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        json_str = report.model_dump_json()
        parsed = json.loads(json_str)
        patient_name = parsed["patient"]["name"]
        assert "value" in patient_name
        assert "confidence" in patient_name
        assert "source_ref" in patient_name
        assert "document_type" in patient_name["source_ref"]

    def test_all_fields_have_value_confidence_source(self, extractor: ICSRExtractor):
        report = extractor.extract(COMPLETE_REPORT, filename="report.pdf")
        json_str = report.model_dump_json()
        parsed = json.loads(json_str)

        def check_field(obj, path=""):
            if isinstance(obj, dict):
                if "value" in obj and "confidence" in obj and "source_ref" in obj:
                    return True
                for k, v in obj.items():
                    if check_field(v, f"{path}.{k}"):
                        return True
            return False

        # Check patient fields
        for field_name in ["name", "age", "sex", "weight", "height", "medical_history"]:
            field = parsed["patient"][field_name]
            assert "value" in field, f"patient.{field_name} missing 'value'"
            assert "confidence" in field, f"patient.{field_name} missing 'confidence'"
            assert "source_ref" in field, f"patient.{field_name} missing 'source_ref'"

    def test_partial_report_json(self, extractor: ICSRExtractor):
        report = extractor.extract(PARTIAL_REPORT, filename="partial.pdf")
        json_str = report.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["patient"]["weight"]["value"] == "Not stated"
        assert parsed["patient"]["weight"]["confidence"] == 0.0
        assert parsed["patient"]["name"]["value"] == "Test Subject B"
        assert parsed["patient"]["name"]["confidence"] > 0.0
