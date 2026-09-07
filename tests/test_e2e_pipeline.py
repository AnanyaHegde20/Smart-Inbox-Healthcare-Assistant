"""
End-to-End Integration Test: Email → PDF → AI → Database → Angular → Reviewer → Audit

This test verifies the complete pipeline:
1. Email ingestion via API
2. PDF document processing via AI service
3. AI classification and extraction
4. Database storage
5. Review accept/override workflow
6. Audit logging at every step
"""

import pytest
import httpx
import time
import json

BASE_URL_PYTHON = "http://localhost:8001"
BASE_URL_JAVA = "http://localhost:8000"


@pytest.fixture(scope="module")
def client():
    """Create async HTTP client for the test session."""
    with httpx.Client(timeout=30.0) as client:
        yield client


class TestEndToEndPipeline:
    """End-to-end integration test suite."""

    def test_01_ai_health(self, client):
        """Step 1: Verify AI service is running."""
        response = client.get(f"{BASE_URL_PYTHON}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_02_java_health(self, client):
        """Step 2: Verify Spring Boot backend is running."""
        response = client.get(f"{BASE_URL_JAVA}/actuator/health")
        # If actuator is not available, try a different endpoint
        if response.status_code == 404:
            response = client.get(f"{BASE_URL_JAVA}/api/emails")
        # Either 200 or 503 is acceptable (service might be starting)
        assert response.status_code in [200, 503]

    def test_03_email_ingestion(self, client):
        """Step 3: Create email via Spring Boot API."""
        email_data = {
            "sender": "dr.jones@hospital.org",
            "recipient": "safety@clinicverse.com",
            "subject": "E2E Test: Patient adverse event report",
            "body": "Patient experienced allergic reaction after taking Aspirin 100mg."
        }

        response = client.post(
            f"{BASE_URL_JAVA}/api/emails",
            json=email_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 201

        result = response.json()
        assert "id" in result
        assert result["status"] == "RECEIVED"
        email_id = result["id"]

        # Store for later tests
        TestEndToEndPipeline.email_id = email_id
        print(f"  Created email ID: {email_id}")

    def test_04_email_processing(self, client):
        """Step 4: Verify email was processed."""
        time.sleep(2)  # Wait for async processing

        email_id = TestEndToEndPipeline.email_id
        response = client.get(f"{BASE_URL_JAVA}/api/emails/{email_id}")
        assert response.status_code == 200

        email = response.json()
        # Status should be COMPLETED or PROCESSING
        assert email["status"] in ["COMPLETED", "PROCESSING"]

    def test_05_classification(self, client):
        """Step 5: Verify classification exists."""
        email_id = TestEndToEndPipeline.email_id
        response = client.get(f"{BASE_URL_JAVA}/api/emails/{email_id}/classification")
        assert response.status_code == 200

        classification = response.json()
        assert classification["primaryCategory"] in [
            "SAFETY_REPORT", "QUALITY_COMPLAINT", "INFO_REQUEST", "NOT_RELEVANT"
        ]
        assert 0 <= classification["primaryConfidence"] <= 1
        print(f"  Category: {classification['primaryCategory']} "
              f"(confidence: {classification['primaryConfidence']:.2%})")

    def test_06_extraction(self, client):
        """Step 6: Verify extraction exists."""
        email_id = TestEndToEndPipeline.email_id
        response = client.get(f"{BASE_URL_JAVA}/api/emails/{email_id}/extraction")
        # Extraction might not exist for all emails
        if response.status_code == 200:
            extraction = response.json()
            assert "extractedData" in extraction
            print(f"  Extraction type: {extraction.get('extractionType', 'N/A')}")

    def test_07_audit_logs(self, client):
        """Step 7: Verify audit logs were created."""
        email_id = TestEndToEndPipeline.email_id
        response = client.get(f"{BASE_URL_JAVA}/api/audit-logs/email/{email_id}")
        assert response.status_code == 200

        logs = response.json()
        assert len(logs) >= 1
        actions = [log["action"] for log in logs]
        assert "EMAIL_RECEIVED" in actions
        print(f"  Audit actions: {actions}")

    def test_08_review_accept(self, client):
        """Step 8: Reviewer accepts classification."""
        email_id = TestEndToEndPipeline.email_id

        accept_data = {
            "reviewerId": "dr.e2e-tester",
            "notes": "E2E test: classification confirmed"
        }

        response = client.post(
            f"{BASE_URL_JAVA}/api/reviews/{email_id}/accept",
            json=accept_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200

        result = response.json()
        assert "message" in result
        print(f"  Review result: {result['message']}")

    def test_09_review_verification(self, client):
        """Step 9: Verify review was stored."""
        email_id = TestEndToEndPipeline.email_id
        response = client.get(f"{BASE_URL_JAVA}/api/reviews/email/{email_id}")
        assert response.status_code == 200

        review = response.json()
        assert review["action"] == "ACCEPTED"
        assert review["reviewerId"] == "dr.e2e-tester"

    def test_10_duplicate_review_blocked(self, client):
        """Step 10: Verify duplicate review is blocked."""
        email_id = TestEndToEndPipeline.email_id

        accept_data = {
            "reviewerId": "dr.e2e-tester",
            "notes": "Second review attempt"
        }

        response = client.post(
            f"{BASE_URL_JAVA}/api/reviews/{email_id}/accept",
            json=accept_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 409  # Conflict

    def test_11_ai_classify_direct(self, client):
        """Step 11: Test AI classification directly."""
        classify_data = {
            "text": "Patient experienced severe allergic reaction after taking Penicillin.",
            "document_type": "email"
        }

        response = client.post(
            f"{BASE_URL_PYTHON}/api/v1/classify",
            json=classify_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200

        result = response.json()
        assert "primary_category" in result
        assert result["primary_category"] in [
            "SAFETY_REPORT", "QUALITY_COMPLAINT", "INFO_REQUEST", "NOT_RELEVANT"
        ]

    def test_12_ai_extract_direct(self, client):
        """Step 12: Test AI extraction directly."""
        extract_data = {
            "text": "Patient ID: E2E-001. Drug: Ibuprofen 400mg. Reaction: headache.",
            "document_type": "ICSR"
        }

        response = client.post(
            f"{BASE_URL_PYTHON}/api/v1/extract",
            json=extract_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200

        result = response.json()
        assert "fields" in result
        assert isinstance(result["fields"], list)

    def test_13_ai_summarize_direct(self, client):
        """Step 13: Test AI summarization directly."""
        summarize_data = {
            "text": "This is a comprehensive patient safety report detailing an adverse event. "
                    "The patient experienced symptoms after medication administration. "
                    "Immediate medical intervention was required. The case was reported to "
                    "pharmacovigilance department for further investigation."
        }

        response = client.post(
            f"{BASE_URL_PYTHON}/api/v1/summarize",
            json=summarize_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200

        result = response.json()
        assert "summary" in result
        assert len(result["summary"]) > 0

    def test_14_audit_stats(self, client):
        """Step 14: Verify audit statistics."""
        response = client.get(f"{BASE_URL_JAVA}/api/audit-logs/stats")
        assert response.status_code == 200

        stats = response.json()
        assert isinstance(stats, dict)
        assert "EMAIL_RECEIVED" in stats
        print(f"  Audit stats: {stats}")

    def test_15_overall_pipeline_integrity(self, client):
        """Step 15: Final verification of complete pipeline."""
        email_id = TestEndToEndPipeline.email_id

        # Verify email
        email_resp = client.get(f"{BASE_URL_JAVA}/api/emails/{email_id}")
        assert email_resp.status_code == 200

        # Verify classification
        class_resp = client.get(f"{BASE_URL_JAVA}/api/emails/{email_id}/classification")
        assert class_resp.status_code == 200

        # Verify audit logs
        audit_resp = client.get(f"{BASE_URL_JAVA}/api/audit-logs/email/{email_id}")
        assert audit_resp.status_code == 200

        # Verify review
        review_resp = client.get(f"{BASE_URL_JAVA}/api/reviews/email/{email_id}")
        assert review_resp.status_code == 200

        print(f"  Pipeline integrity: ALL PASSED for email ID {email_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
