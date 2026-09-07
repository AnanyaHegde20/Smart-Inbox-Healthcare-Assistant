#!/usr/bin/env python3
"""
Synthetic Test PDF Generator for Smart Inbox Assistant Healthcare.

Generates all required test PDF files:
- 5 digital text-based PDF reports
- 2 scanned/image-based PDFs (for OCR testing)
- 5 fictional article PDFs
- 2 non-English PDFs (Spanish, French)
- 2 quality complaint PDFs
- 2 info request PDFs
- 1 irrelevant/marketing PDF

ALL DATA IS SYNTHETIC. No real patient information.

Usage:
    python test-data/generate_test_pdfs.py
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# ReportLab imports for text-based PDFs
# ---------------------------------------------------------------------------
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, gray, white, HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ---------------------------------------------------------------------------
# Pillow + PyMuPDF for image-based (scanned) PDFs
# ---------------------------------------------------------------------------
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PDF_DIR = SCRIPT_DIR / "pdfs"

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "CustomTitle", parent=styles["Title"], fontSize=16, spaceAfter=12,
    textColor=HexColor("#1a237e"),
)
HEADING_STYLE = ParagraphStyle(
    "CustomHeading", parent=styles["Heading2"], fontSize=12, spaceAfter=8,
    textColor=HexColor("#283593"),
)
BODY_STYLE = ParagraphStyle(
    "CustomBody", parent=styles["Normal"], fontSize=10, leading=14,
    alignment=TA_JUSTIFY, spaceAfter=6,
)
SMALL_STYLE = ParagraphStyle(
    "Small", parent=styles["Normal"], fontSize=8, leading=10,
    textColor=gray,
)
FIELD_STYLE = ParagraphStyle(
    "Field", parent=styles["Normal"], fontSize=10, leading=13, spaceAfter=3,
)


# ===========================================================================
# Helper: text-based PDF via ReportLab
# ===========================================================================

def make_text_pdf(path: Path, title: str, sections: list, pages: int = 1):
    """Create a text-based PDF with title and sections.

    sections: list of (heading_or_None, content_string)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path), pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    story = []
    story.append(Paragraph(title, TITLE_STYLE))
    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#1a237e")))
    story.append(Spacer(1, 0.15 * inch))

    for heading, content in sections:
        if heading:
            story.append(Paragraph(heading, HEADING_STYLE))
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.05 * inch))
            elif line.startswith("|"):
                # Simple table row
                story.append(Paragraph(f"<font face='Courier'>{line}</font>", FIELD_STYLE))
            else:
                story.append(Paragraph(line, BODY_STYLE))
        story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    print(f"  [OK] {path.relative_to(SCRIPT_DIR)}")


# ===========================================================================
# Helper: image-based (scanned) PDF via Pillow + PyMuPDF
# ===========================================================================

def make_scanned_pdf(path: Path, lines: list, font_size: int = 16,
                     img_width: int = 2480, img_height: int = 3508,
                     noise: bool = False, skew_deg: float = 0.0):
    """Create an image-only PDF (no selectable text) for OCR testing.

    Renders text onto a white image, then embeds as PDF page.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Build multi-page PDF
    doc = fitz.open()
    _render_scanned_pages(doc, lines, font_size, img_width, img_height, noise, skew_deg)
    doc.save(str(path))
    doc.close()
    print(f"  [OK] {path.relative_to(SCRIPT_DIR)} (scanned/image-based)")


def _render_scanned_pages(doc, lines, font_size, img_width, img_height, noise, skew_deg):
    """Render text lines into image pages and append to fitz document."""
    page_lines = []
    for line in lines:
        if line == "---PAGEBREAK---":
            if page_lines:
                _append_image_page(doc, page_lines, font_size, img_width, img_height, noise, skew_deg)
                page_lines = []
        else:
            page_lines.append(line)
    if page_lines:
        _append_image_page(doc, page_lines, font_size, img_width, img_height, noise, skew_deg)


def _append_image_page(doc, page_lines, font_size, img_width, img_height, noise, skew_deg):
    """Render a single page of lines into an image and add to doc."""
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    y = 100
    for line in page_lines:
        draw.text((80, y), line, fill="black", font=font)
        y += font_size + 12

    if noise:
        _add_noise(img)
    if skew_deg:
        img = img.rotate(skew_deg, expand=True, fillcolor="white")

    # Save image to temp bytes, then insert into PDF page
    import io
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # Create a new page and insert the image
    rect = fitz.Rect(0, 0, img_width * 0.75, img_height * 0.75)  # 96 DPI
    page = doc.new_page(width=rect.width, height=rect.height)
    page.insert_image(rect, stream=img_bytes.getvalue())


def _add_noise(img):
    """Add subtle noise to simulate scan artifacts."""
    import random
    pixels = img.load()
    w, h = img.size
    for _ in range(int(w * h * 0.001)):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        r, g, b = pixels[x, y]
        offset = random.randint(-20, 20)
        pixels[x, y] = (
            max(0, min(255, r + offset)),
            max(0, min(255, g + offset)),
            max(0, min(255, b + offset)),
        )


# ===========================================================================
# 1. DIGITAL PDF REPORTS
# ===========================================================================

def generate_digital_pdfs():
    print("\n=== Generating Digital PDF Reports ===")

    # digital-01: ICSR Report
    make_text_pdf(
        PDF_DIR / "digital" / "digital-01-icsr-report.pdf",
        "INDIVIDUAL CASE SAFETY REPORT (ICSR)",
        [
            ("Report Information", """
Report Reference: MSR-2025-0923
Report Type: Initial Report
Source: Healthcare Professional
Date of Report: 2025-08-20
Reporter: Dr. Patricia Morales, MD, Internal Medicine
Facility: Valley View Medical Center
Contact: p.morales@valleyview-med.org | (555) 321-4567
"""),
            ("Patient Information", """
Patient Initials: A.B.
Date of Birth: 04/12/1968
Sex: Male
Weight: 78 kg
Height: 178 cm
Medical History: Hypertension (2018), Hyperlipidemia
No known drug allergies prior to this event.
"""),
            ("Suspect Product", """
Product Name: CardioShield 40mg Tablets
Manufacturer: HeartCare Pharmaceuticals
Lot Number: HC-2025-0789
NDC: 56789-012-34
Dose: 40mg once daily
Route: Oral
Indication: Hypertension
"""),
            ("Event Description", """
Patient developed progressive muscle weakness starting 3 days after
initiating CardioShield 40mg. By day 7, patient reported difficulty
climbing stairs and lifting objects. CK levels elevated to 2,450 U/L
(normal: 22-198 U/L).

Onset Date: 2025-08-15
Resolution Date: Ongoing
Outcome: Not recovered
Event Serious: Yes
Criteria: Other medically important condition
"""),
            ("Concomitant Medications", """
1. Lisinopril 20mg daily (since 2019)
2. Atorvastatin 40mg daily (since 2020)
"""),
            ("Treatment and Outcome", """
CardioShield discontinued on 2025-08-22.
CK levels monitored weekly. Physical therapy initiated.
Causality Assessment: Probable
Rationale: Temporal relationship, dechallenge positive
"""),
        ],
    )

    # digital-02: Discharge Summary
    make_text_pdf(
        PDF_DIR / "digital" / "digital-02-discharge-summary.pdf",
        "RIVERSIDE GENERAL HOSPITAL - DISCHARGE SUMMARY",
        [
            ("Patient Information", """
Patient: Margaret Chen
DOB: 07/22/1945
MRN: SYN-890123
Admission Date: 2025-08-10
Discharge Date: 2025-08-17
Attending Physician: Dr. Robert Anderson, MD
"""),
            ("Admitting Diagnosis", """
Acute exacerbation of chronic heart failure (NYHA Class III)
"""),
            ("Hospital Course", """
Patient presented with 3-day history of progressive dyspnea, lower
extremity edema, and weight gain of 4 kg over 2 weeks.

Echocardiogram: EF 30% (baseline 35% 6 months ago).
BNP: 2,840 pg/mL on admission.

Treatment:
- IV Furosemide 40mg BID for 4 days
- Daily weight monitoring
- Fluid restriction (1.5L/day)
- Sodium restriction (<2g/day)
- Carvedilol continued at 25mg BID
- Lisinopril uptitrated from 10mg to 20mg daily
"""),
            ("Discharge Medications", """
1. Furosemide 40mg PO daily
2. Carvedilol 25mg PO BID
3. Lisinopril 20mg PO daily
4. Spironolactone 25mg PO daily
5. Aspirin 81mg PO daily
"""),
            ("Discharge Instructions", """
- Weigh yourself daily, same time, same scale
- Call doctor if weight increases >2 kg in 24h or >4 kg in 1 week
- Low sodium diet (<2g daily)
- Fluid restriction: 1.5L daily
- No NSAIDs
- Resume cardiac rehabilitation in 2 weeks
"""),
            ("Follow-up", """
- Cardiology: 2 weeks post-discharge
- Primary Care: 1 week post-discharge
- Labs: BMP in 1 week
Condition at Discharge: Stable, ambulatory, SpO2 96% on room air
"""),
        ],
    )

    # digital-03: Medication Error Report
    make_text_pdf(
        PDF_DIR / "digital" / "digital-03-medication-error.pdf",
        "CITY HOSPITAL - MEDICATION ERROR REPORT",
        [
            ("Incident Summary", """
Report Date: 2025-08-18
Report Number: MER-2025-0342
Reported By: James O'Malley, PharmD, Director of Pharmacy
Date of Error: 2025-08-17
Time Discovered: 14:45
Location: Pharmacy Department, Station 2
"""),
            ("Patient Information", """
Name: Jane Smith (pseudonym)
DOB: 05/22/1975
MRN: SYN-789012
Room: 412B
Attending: Dr. Williams
"""),
            ("Error Details", """
Error Type: Wrong dose dispensed
Medication: Warfarin
Prescribed Dose: 2.5mg
Dispensed Dose: 5.0mg
Route: Oral
"""),
            ("Contributing Factors", """
1. Look-alike packaging (2.5mg and 5mg stored adjacent)
2. Barcode scanner malfunction (out of service for 3 hours)
3. Pharmacist staffing: 1 pharmacist covering 2 stations
4. High workload: 47 prescriptions pending
"""),
            ("Error Detection", """
Detected By: Patricia Lee, RN
Detection Method: Independent double-check at bedside
Time to Detection: After 1 dose administered
"""),
            ("Patient Impact", """
- One dose of 5mg warfarin administered (intended: 2.5mg)
- INR checked: 3.2 (therapeutic range 2.0-3.0)
- No bleeding events
- Vitamin K 2.5mg PO administered prophylactically
- Patient monitored for 24 hours
"""),
            ("Corrective Actions", """
Action                          | Responsible           | Due Date | Status
Replace barcode scanner         | Biomed Engineering    | 08/18    | Complete
Separate warfarin strengths     | Pharmacy Manager      | 08/19    | Complete
Staff retraining on LASA        | Education Dept        | 08/25    | In Progress
Independent double-check        | Pharmacy Director     | 08/30    | Planned
Review staffing model           | Operations Manager    | 09/15    | Planned
"""),
        ],
    )

    # digital-04: Lab Results
    make_text_pdf(
        PDF_DIR / "digital" / "digital-04-lab-results.pdf",
        "VALLEY VIEW MEDICAL CENTER - Laboratory Report",
        [
            ("Patient Information", """
Patient: Marcus Thornton
DOB: 03/15/1958
MRN: SYN-44721
Collection Date: 2025-08-12
Ordering Physician: Dr. Elena Vasquez
"""),
            ("Complete Blood Count (CBC)", """
Component          Result    Units         Reference Range
-----------------------------------------------------------
WBC                12.4      x10^3/uL      4.5-11.0       HIGH
RBC                4.8       x10^6/uL      4.5-5.5
Hemoglobin         14.2      g/dL          13.5-17.5
Hematocrit         42.1      %             38.3-48.6
MCV                87.7      fL            80.0-100.0
Platelet Count     245       x10^3/uL      150-400
Neutrophils        78        %             40-70          HIGH
Lymphocytes        15        %             20-40          LOW
"""),
            ("Basic Metabolic Panel", """
Component          Result    Units         Reference Range
-----------------------------------------------------------
Glucose            142       mg/dL         70-100         HIGH
BUN                18        mg/dL         7-20
Creatinine         1.1       mg/dL         0.7-1.3
Sodium             140       mEq/L         136-145
Potassium          4.2       mEq/L         3.5-5.0
Chloride           102       mEq/L         98-106
CO2                24        mEq/L         23-29
Calcium            9.4       mg/dL         8.5-10.5
"""),
            ("Lipid Panel", """
Component          Result    Units         Reference Range
-----------------------------------------------------------
Total Cholesterol  218       mg/dL         <200           HIGH
LDL                142       mg/dL         <100           HIGH
HDL                38        mg/dL         >40            LOW
Triglycerides      195       mg/dL         <150           HIGH
"""),
            ("Clinical Significance", """
Elevated WBC and neutrophils may indicate acute stress response
or early infection. Lipid panel shows dyslipidemia - consider
medication adjustment. Glucose elevated - fasting specimen
not confirmed.
Electronically verified by: Dr. Sarah Kim, MD, Pathology
"""),
        ],
    )

    # digital-05: Quality Audit
    make_text_pdf(
        PDF_DIR / "digital" / "digital-05-quality-audit.pdf",
        "PHARMACURE LABORATORIES - Internal Quality Audit Report",
        [
            ("Audit Information", """
Audit Reference: QA-2025-0078
Audit Date: 2025-08-15 to 2025-08-16
Audit Type: Annual GMP Compliance Audit
Lead Auditor: Jennifer Wu, Quality Control Manager
Scope: Manufacturing operations, Building 2, Lines 1-4
Overall Rating: SATISFACTORY with observations
Total Findings: 12 (Critical: 0, Major: 3, Minor: 9)
"""),
            ("Finding #1 - MAJOR", """
Category: Documentation
Area: Packaging Department
Description: Batch packaging records for Lot PC-2025-3201 show
  unsigned entries for in-process checks on 2025-08-10.
Requirement: 21 CFR 211.188
Corrective Action Due: 2025-09-15
"""),
            ("Finding #2 - MAJOR", """
Category: Equipment
Area: Tablet Press Line 2
Description: Preventive maintenance log shows Tablet Press TP-02
  was not calibrated per schedule. Last calibration: 2025-05-20
  (due: 2025-08-01).
Requirement: 21 CFR 211.68
Corrective Action Due: 2025-09-01
"""),
            ("Finding #3 - MAJOR", """
Category: Personnel
Area: Warehouse
Description: 4 warehouse staff have expired forklift certification
  (expired 2025-07-31).
Requirement: SOP-WH-003, OSHA 1910.178
Corrective Action Due: 2025-08-31
"""),
            ("Minor Findings (#4-#12)", """
#4 HVAC excursion to 76F in Room 204 (spec: 68-72F), 45 min
#5 SOP-QC-012 rev 7 not distributed to all analysts
#6 Two drums of Avicel PH-102 missing secondary labels
#7-12 Additional minor documentation and labeling observations
"""),
            ("Corrective Action Summary", """
Finding | Type | Action                          | Owner         | Due     | Status
#1      | Major| Secondary review for pkg records | QA Manager    | 09/15   | Open
#2      | Major| Calibrate TP-02, review PM       | Engineering   | 09/01   | In Progress
#3      | Major| Recertify warehouse staff        | HR/Training   | 08/31   | In Progress
#4      | Minor| HVAC inspection                  | Facilities    | 09/30   | Open
#5      | Minor| Distribute current SOP rev       | Doc Control   | 09/15   | Open
#6      | Minor| Relabel affected material        | Warehouse Mgr | 09/01   | Open
"""),
            ("Conclusion", """
The facility demonstrates overall compliance with GMP requirements.
The three major findings require immediate attention and corrective
action plans should be submitted within 15 business days.

Audit Report Approved By: Jennifer Wu, QC Manager
Date: 2025-08-20
"""),
        ],
    )


# ===========================================================================
# 2. SCANNED / HANDWRITTEN-STYLE PDFs (image-based for OCR)
# ===========================================================================

def generate_scanned_pdfs():
    print("\n=== Generating Scanned/Image-Based PDFs ===")

    # scanned-01: Handwritten incident report
    make_scanned_pdf(
        PDF_DIR / "scanned" / "scanned-01-incident-report.pdf",
        [
            "INCIDENT REPORT FORM",
            "Meridian General Hospital",
            "",
            "Date: Aug 11, 2025        Ward: 3B",
            "Patient: Marcus Thorn... (last name unclear)",
            "Time: approx 2:30 PM",
            "",
            "DESCRIPTION OF INCIDENT:",
            "Patient found on floor next to bed. Bed rails were up.",
            "Call bell was within reach but not activated.",
            "Patient says he was trying to go to bathroom.",
            "Did not call for help. No visible injuries.",
            "VS stable. Patient had fallen asleep in chair",
            "and tried to get up without assistance.",
            "",
            "Witness: David Kim (CNA)",
            "Nurse: Angela Torres, RN",
            "",
            "Assessment:",
            "Patient ambulatory x1 with walker.",
            "Morse Fall Scale score 45 (high risk).",
            "Currently on Metoprolol and Diazepam.",
            "Neuro checks q4h x24h.",
            "",
            "Actions Taken:",
            "1. Dr. Vasquez notified",
            "2. Family called - (555) 012-7890",
            "3. Fall precautions initiated",
            "4. Incident report to Risk Management",
            "",
            "Notes: Patient embarrassed. States he should have",
            "waited for help. Will reinforce call bell use.",
            "",
            "[Signature illegible]",
            "RECEIVED BY RISK MANAGEMENT",
            "Date stamp: AUG 13 2025",
        ],
        font_size=18,
        noise=True,
        skew_deg=0.5,
    )

    # scanned-02: Faxed quality complaint
    make_scanned_pdf(
        PDF_DIR / "scanned" / "scanned-02-faxed-complaint.pdf",
        [
            "FAX TRANSMISSION",
            "From: PharmaCure Laboratories Quality Dept",
            "To: ClinicVerse Complaints Department",
            "Date: 08/20/2025 14:32    Pages: 1/1",
            "Re: Quality Complaint QC-2025-1204",
            "",
            "QUALITY COMPLAINT FORM",
            "",
            "Complaint #: QC-2025-1204",
            "Date Received: 08/20/2025",
            "Priority: HIGH",
            "",
            "Reporter: Jennifer Wu, QC Manager",
            "Company: PharmaCure Labs",
            "Phone: (555) 987-6543",
            "Email: j.wu@pharma-cure.com",
            "",
            "Product: Neurocalm 25mg Tablets",
            "Lot #: PC-2025-3391",
            "NDC: 12345-678-90",
            "",
            "Description of Problem:",
            "Approximately 15% of tablets show uneven coating.",
            "Coating measured 25-45 microns vs spec of 50-80.",
            "Mottled appearance on affected tablets.",
            "",
            "[X] Performance impact suspected",
            "[X] Product quarantined",
            "",
            "Attachments Referenced:",
            "[1] Inspection_Report.pdf",
            "[2] Measurement_Data.xlsx",
            "",
            "Follow up needed - J.W.",
            "TRANSMISSION SUCCESSFUL",
        ],
        font_size=18,
        noise=True,
        skew_deg=-0.3,
    )


# ===========================================================================
# 3. FICTIONAL ARTICLE PDFs
# ===========================================================================

def generate_article_pdfs():
    print("\n=== Generating Fictional Article PDFs ===")

    # article-01: Fall Prevention
    make_text_pdf(
        PDF_DIR / "articles" / "article-01-fall-prevention.pdf",
        "Journal of Patient Safety & Risk Management",
        [
            ("Article Information", """
Volume 28, Issue 3, pp. 145-158 (2025)

Falls in Acute Care Settings: A Comprehensive Review of
Risk Factors and Prevention Strategies

Authors:
Sarah Mitchell, RN, PhD - School of Nursing, Meridian University
David Park, MD, MPH - Dept of Internal Medicine, City General Hospital
Elena Rodriguez, PharmD - Dept of Pharmacy, Valley Medical Center
"""),
            ("Abstract", """
Background: Falls remain one of the most common patient safety
events in acute care hospitals, with rates ranging from 2.2 to 8.3
falls per 1,000 patient days.

Methods: Systematic search of PubMed, CINAHL, and Cochrane Library
for studies published 2018-2024. 42 studies met inclusion criteria.

Results: Key modifiable risk factors: medication effects (OR 2.3),
mobility impairment (OR 3.1), environmental hazards (OR 1.7).
Multifactorial interventions showed greatest effectiveness (RR 0.62).

Conclusions: Evidence supports multifactorial fall prevention programs
combining medication review, environmental modifications, and
patient education.
"""),
            ("Case Example - Fictional Patient", """
Patient: Harold M. Thompson, 72-year-old male
Admission: Elective hip replacement, City General Hospital
Fall Date: Day 3 post-operative

Circumstances: Patient arose from bed at 02:15 AM to use restroom
without calling for nurse. Bed alarm activated. Patient found on
floor by nursing assistant. No injuries detected. Morse Fall Scale
score: 55 (high risk).

Risk Factors Identified:
- Post-surgical mobility impairment
- Sedative use (oxazepam 15mg at bedtime)
- History of falls (2 previous)
- Cognitive impairment (MMSE 24/30)

Intervention: 1:1 observation, fall precautions, toileting schedule,
medication review by pharmacist.
Outcome: No further falls during stay. Discharged with home care.
"""),
            ("Evidence-Based Recommendations", """
1. Implement multifactorial fall prevention programs (Strong evidence)
2. Conduct pharmacist-led medication review within 48 hours
3. Initiate early mobilization protocols
4. Ensure consistent environmental safety measures
5. Provide patient and family education
6. Use validated fall risk assessment tools
"""),
        ],
    )

    # article-02: Medication Reconciliation
    make_text_pdf(
        PDF_DIR / "articles" / "article-02-medication-reconciliation.pdf",
        "Clinical Practice Guideline - American College of Clinical Pharmacy",
        [
            ("Article Information", """
Journal of Clinical Pharmacy and Therapeutics
Volume 51, Issue 2, Pages 89-102 (2025)

Medication Reconciliation in Hospitalized Patients:
2025 Updated Recommendations

Authors:
Robert Chen, PharmD, BCPS - Riverside Medical Center
Patricia Martinez, MD - Stanford University Medical Center
Thomas Anderson, PharmD, MBA - University of Michigan
"""),
            ("Abstract", """
Medication reconciliation is a critical process for preventing
medication errors during care transitions. This guideline provides
updated recommendations based on systematic evidence review and
expert consensus. Key changes from the 2021 edition include
integration of electronic health record-based reconciliation
tools, patient engagement strategies, and outcome measurement.
"""),
            ("Case Example - Fictional Patient", """
Patient: Dorothy R. Williams, 68-year-old female
Admission: Pneumonia, Riverside Medical Center

Medication History Obtained:
- Lisinopril 20mg daily
- Metformin 1000mg BID
- Warfarin 5mg daily (home INR 2.5)
- Aspirin 81mg daily
- Albuterol PRN

Reconciliation Findings:
1. Warfarin dose discrepancy: home bottle says 5mg, but
   medical record shows 2.5mg. Pharmacist contacted patient's
   daughter who confirmed 5mg is correct.
2. Aspirin not listed in hospital formulary order set - added.
3. Metformin held on admission due to elevated creatinine (1.4).
   Reconciled to resume when creatinine <1.3.

Outcome: Zero medication discrepancies at discharge.
Patient educated on changes. Follow-up INR scheduled.
"""),
            ("Recommendations", """
GRADE A (Strong):
- Obtain medication history within 24 hours of admission
- Pharmacist-led reconciliation at transitions of care
- Patient engagement in reconciliation process

GRADE B (Moderate):
- Electronic health record reconciliation tools
- Discrepancy resolution documentation
- Post-discharge follow-up phone call
"""),
        ],
    )

    # article-03: Adverse Drug Reactions
    make_text_pdf(
        PDF_DIR / "articles" / "article-03-adverse-drug-reaction.pdf",
        "British Journal of Clinical Pharmacology - Original Research",
        [
            ("Article Information", """
Received: January 15, 2025
Accepted: June 20, 2025
Published online: August 1, 2025

Incidence and Predictors of Adverse Drug Reactions in
Hospitalized Elderly Patients: A Prospective Cohort Study

Authors:
Michael Thompson, MD, PhD - London Royal Hospital
Anna Kowalski, PharmD - University of Manchester
Jennifer Lee, RN, PhD - King's College London
Hiroshi Tanaka, MD - Tokyo Medical University
"""),
            ("Abstract", """
Objective: To determine the incidence and predictors of adverse
drug reactions (ADRs) in hospitalized elderly patients.

Methods: Prospective cohort study of 1,247 patients aged 65+
admitted to two teaching hospitals over 12 months.

Results: ADR incidence was 18.3% (228/1,247). Most common
agents: anticoagulants (23%), antibiotics (19%), opioids (15%).
Independent predictors: polypharmacy (OR 2.8), renal impairment
(OR 2.1), history of ADR (OR 3.4), age >80 (OR 1.7).
"""),
            ("Case Vignette - Fictional Patient", """
Patient: George P. Harrison, 82-year-old male
Admission: Hip fracture repair

Medications on Admission:
1. Warfarin 3mg daily (for atrial fibrillation)
2. Digoxin 0.125mg daily
3. Furosemide 40mg daily
4. Amlodipine 5mg daily
5. Omeprazole 20mg daily
6. Paracetamol 1g QDS PRN

ADR Event: On day 4 post-surgery, patient developed confusion,
nausea, and visual disturbances. Digoxin level: 2.8 ng/mL
(therapeutic: 0.5-2.0).

Root Cause: Acute kidney injury from post-surgical dehydration
reduced digoxin clearance. Furosemide dose not adjusted.

Management: Digoxin withheld, IV fluids initiated, renal function
monitored. Recovery in 48 hours.

Lesson: Drug level monitoring essential when renal function changes.
"""),
            ("Conclusions", """
ADRs are common in elderly inpatients and significantly prolong
hospital stay. Polypharmacy and renal impairment are major
predictors. Pharmacist-led medication review reduces ADR risk.
"""),
        ],
    )

    # article-04: Antibiotic Stewardship
    make_text_pdf(
        PDF_DIR / "articles" / "article-04-antibiotic-stewardship.pdf",
        "Infection Control & Hospital Epidemiology - Review Article",
        [
            ("Article Information", """
Antibiotic Stewardship in Acute Care Hospitals:
Current Challenges and Future Directions

Authors:
Maria Santos, MD, PhD - University Medical Center
William Chen, PharmD, BCIDP - St. Luke's Hospital
Sarah Johnson, RN, CIC - Metro Health System
"""),
            ("Abstract", """
Antibiotic resistance accounts for 2.8 million infections and
35,000 deaths annually in the US. 30-50% of hospital antibiotics
are unnecessary or inappropriate. This review examines current
challenges in ASP implementation and proposes frameworks for
next-generation stewardship programs.
"""),
            ("Case Example - Fictional Hospital", """
Memorial Community Hospital - ASP Implementation

Baseline Data (Pre-ASP):
- Total antibiotic use: 852 DOT/1000 patient-days
- Broad-spectrum ratio: 42%
- C. difficile rate: 8.2/10,000 patient-days
- MRSA bacteremia: 1.8/10,000 patient-days

Interventions Implemented:
1. Prospective audit with pharmacist intervention
2. Electronic clinical decision support
3. IV-to-oral conversion protocol
4. Cultures-before-antibiotics requirement

Results After 12 Months:
- Total antibiotic use: 687 DOT/1000 patient-days (-19%)
- Broad-spectrum ratio: 28% (-14%)
- C. difficile rate: 4.1/10,000 (-50%)
- MRSA bacteremia: 1.1/10,000 (-39%)
- Cost savings: $340,000 annually
"""),
            ("Key Strategies", """
1. Prospective audit and feedback
2. Formulary restriction and preauthorization
3. Clinical decision support systems
4. De-escalation protocols
5. IV-to-oral conversion
6. Duration optimization
7. Diagnostic stewardship
"""),
        ],
    )

    # article-05: Rare Adverse Event
    make_text_pdf(
        PDF_DIR / "articles" / "article-05-rare-adverse-event.pdf",
        "Journal of Medical Case Reports",
        [
            ("Article Information", """
Drug-induced autoimmune hemolytic anemia associated with
piperacillin-tazobactam: a case report and systematic review

Authors:
Elena Petrov, MD - National University Hospital
James Wilson, MD - City Medical Center
Li Wei, MD, PhD - University Hospital

Corresponding author: e.petrov@nuh.edu.sg
"""),
            ("Abstract", """
Background: Piperacillin-tazobactam is a widely used broad-spectrum
antibiotic. Drug-induced autoimmune hemolytic anemia (AIHA) is a
rare and potentially life-threatening adverse event.

Case: 62-year-old male developed severe AIHA after 10 days of
piperacillin-tazobactam for hospital-acquired pneumonia.

Presentation: Fatigue, jaundice, dark urine.
Labs: Hemoglobin 6.2 g/dL, reticulocyte count 12.5%,
DAT positive for IgG and C3d, LDH 1,250 U/L.

Treatment: Drug discontinued, corticosteroids initiated.
Hemoglobin normalized over 4 weeks.

Systematic Review: 23 previously reported cases, mortality 8.7%.
"""),
            ("Case Presentation", """
Patient: Robert J. Kellerman, 62-year-old Caucasian male
Medical History: Type 2 diabetes, COPD, chronic kidney disease

Hospital Course:
- Day 1: Admitted with hospital-acquired pneumonia
- Day 1: Started on piperacillin-tazobactam 4.5g IV q6h
- Day 5: Improving respiratory symptoms
- Day 8: Developed fatigue, dark urine
- Day 10: Jaundice noted, hemoglobin dropped to 6.2 g/dL
  (baseline 13.8 g/dL)

Workup:
- Direct antiglobulin test (DAT): Positive for IgG and C3d
- Reticulocyte count: 12.5%
- LDH: 1,250 U/L (normal: 140-280)
- Haptoglobin: <10 mg/dL (normal: 30-200)
- Peripheral smear: Spherocytosis

Diagnosis: Drug-induced autoimmune hemolytic anemia

Management:
1. Piperacillin-tazobactam discontinued immediately
2. Prednisone 1mg/kg/day initiated
3. Transfusion of 2 units PRBC
4. Close monitoring of hemoglobin and renal function

Outcome: Hemoglobin normalized to 12.1 g/dL over 4 weeks.
Prednisone tapered over 8 weeks. No recurrence.
"""),
            ("Discussion", """
Drug-induced AIHA is rare (estimated 1 per 100,000 drug exposures).
Piperacillin-tazobactam is the second most commonly implicated
antibiotic after ceftriaxone. Mechanism involves drug adsorption
onto red blood cell membrane, triggering immune response.

Mortality rate in published cases: 8.7% (2/23).
All fatalities occurred in patients with comorbidities.
Early recognition and drug discontinuation are critical.
"""),
        ],
    )


# ===========================================================================
# 4. NON-ENGLISH PDFs
# ===========================================================================

def generate_non_english_pdfs():
    print("\n=== Generating Non-English PDFs ===")

    # non-english-01: Spanish patient safety report (digital text)
    make_text_pdf(
        PDF_DIR / "non-english" / "non-english-01-spanish.pdf",
        "INFORME DE INCIDENTE DE SEGURIDAD DEL PACIENTE",
        [
            ("Informacion del Hospital", """
Hospital General Metropolitano
Departamento de Calidad y Seguridad

Numero de Reporte: IS-2025-0456
Fecha del Incidente: 2025-08-14
Fecha del Reporte: 2025-08-15
"""),
            ("Informacion del Paciente", """
Nombre: Maria Garcia Lopez (seudonimo)
Fecha de Nacimiento: 22/03/1970
Numero de Expediente: EXP-890123
Servicio: Medicina Interna
Cama: 412-B
"""),
            ("Descripcion del Incidente", """
El paciente fue encontrado en el suelo junto a la cama a las
14:30 horas. La enfermera de guardia, Ana Martinez, RC, fue
alertada por el sistema de monitoreo.

Detalles:
- Paciente intentaba ir al bano sin asistencia
- Barandal de la cama estaba en posicion arriba
- Timbre de llamada estaba al alcance pero no fue utilizado
- Paciente reporta que se resbalo al intentar levantarse
"""),
            ("Evaluacion Inicial", """
- Sin lesiones visibles
- Signos vitales estables
- Conciencia intacta
- Movilidad reducida temporalmente

Medicamentos del Paciente:
1. Metoprolol 50mg dos veces al dia
2. Diazepam 5mg antes de dormir
3. Lisinopril 20mg una vez al dia
"""),
            ("Asistencia Proporcionada", """
1. Paciente asistido de vuelta a la cama
2. Evaluacion post-caida completada
3. Monitoreo neurologico cada 4 horas por 24 horas
4. Notificado al Dr. Vasquez
5. Familia contactada: telefono (555) 012-7890

Evaluacion de Riesgo de Caida:
- Escala Morse: 45 (riesgo alto)
- Factores de riesgo: Medicamentos sedantes, movilidad reducida
"""),
            ("Plan de Accion", """
1. Revisar medicamentos que contribuyen a caidas
2. Evaluar necesidad de asistencia para movilidad
3. Ensennar uso correcto del timbre de llamada
4. Considerar alarma de cama si es necesario
5. Seguimiento diario hasta alta

Resultado: Paciente se recupero sin lesiones. Monitoreo continua.
Reportado por: Ana Martinez, RC
Firmado: Dr. Roberto Vasquez, MD
"""),
        ],
    )

    # non-english-02: French quality complaint (image-based/scanned)
    make_scanned_pdf(
        PDF_DIR / "non-english" / "non-english-02-french.pdf",
        [
            "RAPPORT DE QUALITE",
            "Pharmacie Centrale de Lyon",
            "Service Qualite et Assurance",
            "",
            "Reference: RQ-2025-0789",
            "Date: 25 aout 2025",
            "Priorite: Haute",
            "",
            "PLAINT DE QUALITE - LOT PX-2025-4412",
            "",
            "Plaignant: Dr. Marie Dubois",
            "Service: Pharmacie Hospitaliere",
            "Telephone: 04-72-XX-XX-XX",
            "",
            "Produit: Amoxicilline 500mg gelules",
            "Lot: PX-2025-4412",
            "Date de fabrication: 15/06/2025",
            "Date de peremption: 15/06/2027",
            "",
            "Description du Probleme:",
            "Lors d'un controle de routine, nous avons detecte que",
            "environ 8% des capsules presentent un defaut de fermeture.",
            "La fermeture hermetique n'est pas assuree pour ces",
            "unites, ce qui peut affecter la stabilite du produit.",
            "",
            "Impact:",
            "- 350 boites distribuees a 5 services hospitaliers",
            "- Aucun evenement indesirable signale",
            "- Stock restant en quarantaine",
            "",
            "Mesures Prises:",
            "1. Tout le lot mis en quarantaine",
            "2. Controle de 100% des unites restantes",
            "3. Informe le fabricant (reference: FR-2025-1567)",
            "4. Demande d'analyse de cause racine",
            "",
            "Redacteur: Dr. Marie Dubois, PharmD",
            "Verificate: Prof. Jean-Pierre Martin, PhD",
        ],
        font_size=18,
        noise=True,
        skew_deg=0.4,
    )


# ===========================================================================
# 5. QUALITY COMPLAINT PDFs
# ===========================================================================

def generate_quality_complaint_pdfs():
    print("\n=== Generating Quality Complaint PDFs ===")

    # qc-01: Tablet coating defect
    make_text_pdf(
        PDF_DIR / "quality-complaints" / "qc-01-tablet-coating.pdf",
        "QUALITY COMPLAINT REPORT - PHARMACURE LABORATORIES",
        [
            ("Complaint Information", """
Complaint Reference: QC-2025-1204
Date Received: 2025-08-20
Priority: High
Category: Manufacturing Defect / Product Quality
"""),
            ("Reporter Information", """
Name: Jennifer Wu
Title: Quality Control Manager
Organization: PharmaCure Laboratories
Phone: (555) 987-6543
Email: jennifer.wu@pharma-cure-labs.com
"""),
            ("Product Information", """
Product: Neurocalm 25mg Tablets
NDC: 12345-678-90
Lot Number: PC-2025-3391
Manufacturing Date: 2025-07-01
Expiry: 2027-06-30
Batch Size: 200,000 tablets
"""),
            ("Complaint Description", """
During routine quality inspection, approximately 15% of tablets
in Lot PC-2025-3391 exhibit uneven coating. The coating appears
thinner on one side of the tablet. This may affect dissolution
rates and bioequivalence.

Visual inspection shows mottled appearance on affected tablets.
Standard coating thickness specification: 50-80 microns
Affected tablets measured: 25-45 microns (below specification)
"""),
            ("Impact Assessment", """
- Product distributed to: 3 hospital pharmacies, 12 retail outlets
- No patient adverse events reported to date
- Remaining inventory under quarantine
- Severity: Moderate (potential efficacy impact)
"""),
            ("Investigation Findings", """
Root Cause: Coating pan temperature fluctuation during production
run on 2025-07-01. Temperature controller showed intermittent
drift of +5C above setpoint.

Contributing Factors:
1. Preventive maintenance overdue on temperature controller
2. Operator did not notice alarm threshold breach
3. In-process checks did not include coating thickness
"""),
            ("Requested Action", """
1. Root cause investigation - COMPLETE
2. Recall assessment - NOT REQUIRED (contained to quarantined stock)
3. Corrective action plan:
   a. Recalibrate all coating pan temperature controllers
   b. Add coating thickness to in-process checks
   c. Retrain operators on alarm response
4. Corrective action due within 30 days
"""),
        ],
    )

    # qc-02: Device malfunction
    make_text_pdf(
        PDF_DIR / "quality-complaints" / "qc-02-device-malfunction.pdf",
        "MEDICAL DEVICE MALFUNCTION REPORT",
        [
            ("Report Information", """
Report Reference: DM-2025-0312
Date: 2025-09-01
Facility: Metro General Hospital
Department: Emergency Medicine
Reporter: Sarah Kim, Biomedical Engineer
"""),
            ("Device Information", """
Device: VitaCheck Pulse Oximeter
Model: PX-500
Manufacturer: MedWatch Systems Inc.
Serial Number: PX500-2024-3847
Purchase Date: 2025-02-15
Last Calibration: 2025-05-20
"""),
            ("Malfunction Description", """
During routine use in the Emergency Department, the pulse oximeter
displayed SpO2 reading of 98% for a patient who was subsequently
found to have SpO2 of 89% on arterial blood gas.

The device was used on a patient with:
- Dark skin pigmentation
- Poor peripheral perfusion (cold extremities)
- Hypothermia (core temp 34.2C)

The reading remained at 98% for 15 minutes until the device was
repositioned to a different finger, where it displayed 91%.
"""),
            ("Patient Impact", """
The delayed accurate reading resulted in a 12-minute delay in
initiating supplemental oxygen therapy. Patient recovered without
permanent harm. Incident reported to Risk Management.

Patient condition at time of incident: Stable but hypoxic.
Final outcome: Full recovery after treatment.
"""),
            ("Investigation", """
Preliminary findings:
1. Device was functioning within manufacturer specifications
2. Low perfusion index (0.3%) below device accuracy threshold
3. Manufacturer documentation states accuracy +/-5% when
   perfusion index <0.4%
4. Staff training did not cover perfusion index limitations

Corrective Actions:
1. Issue clinical advisory on device limitations
2. Update staff training to include perfusion index monitoring
3. Consider alternative devices for low-perfusion patients
4. Report to FDA MedWatch as required
"""),
        ],
    )


# ===========================================================================
# 6. INFO REQUEST PDFs
# ===========================================================================

def generate_info_request_pdfs():
    print("\n=== Generating Info Request PDFs ===")

    # ir-01: Storage guidelines
    make_text_pdf(
        PDF_DIR / "info-requests" / "ir-01-storage-guidelines.pdf",
        "INFORMATION REQUEST - MEDICATION STORAGE GUIDELINES",
        [
            ("Request Information", """
Date: 2025-09-01
From: Robert Chen, PharmD
Organization: Riverside Medical Center
Phone: (555) 234-5678
Email: robert.chen@riverside-medical.org
Urgency: Medium
Preferred Response: Written document or reference links
"""),
            ("Subject", """
Request for clarification on insulin product storage requirements
"""),
            ("Specific Questions", """
We are updating our pharmacy's cold chain management protocol and
need authoritative guidance on the following insulin products:

1. Lantus (insulin glargine) - opened vials
2. Humalog (insulin lispro) - opened pens
3. NovoLog (insulin aspart) - unopened cartridges

Questions:
a) What is the maximum room temperature for storage after opening?
b) What is the discard date after first use for each product?
c) Are there any stability studies supporting extended use beyond
   manufacturer guidelines?
d) How should we handle insulin that has been at room temperature
   for an unknown duration?
e) What documentation is required for cold chain deviations?
"""),
            ("Context", """
Our current policy references USP <797> but we want to ensure
alignment with latest manufacturer recommendations. We serve a
rural patient population where patients may have limited access
to replacement insulin supplies.

We would also appreciate any guidance on:
- Patient education materials for home storage
- Documentation requirements for regulatory compliance
- Emergency protocols for cold chain failures
"""),
        ],
    )

    # ir-02: System capabilities
    make_text_pdf(
        PDF_DIR / "info-requests" / "ir-02-system-capabilities.pdf",
        "INQUIRY - SYSTEM CAPABILITIES AND INTEGRATION",
        [
            ("Request Information", """
Date: 2025-09-03
From: Nora Kapoor, Research Coordinator
Organization: Stanford Medical Center
Phone: (650) 555-0142
Email: nora.kapoor@stanford.edu
Timeline: Decision by October 15, 2025
"""),
            ("Subject", """
Questions about platform capabilities for clinical trial support
"""),
            ("Background", """
We are a Phase III clinical trial for a new diabetes medication
(Protocol #SC-2025-DIAB-001) evaluating your platform for
adverse event report management and classification.
"""),
            ("Questions", """
1. Can your platform handle electronic informed consent documents?
2. Do you support integration with REDCap for data capture?
3. What formats do you accept for adverse event reports?
4. Can the classification system be customized for trial-specific
   categories beyond the standard healthcare categories?
5. What is the API rate limit for batch document processing?
6. Do you support multi-language document processing?
7. What audit trail capabilities are available for regulatory
   compliance (21 CFR Part 11)?
8. Can the system generate expedited safety reports (CIOMS forms)?
"""),
            ("Requirements", """
- FDA 21 CFR Part 11 compliance
- HIPAA-compliant data handling
- Real-time classification with <2 second response time
- Support for 10,000+ documents per month
- Integration with existing REDCap instance
- Custom classification categories for trial-specific events
"""),
        ],
    )


# ===========================================================================
# 7. IRRELEVANT PDF
# ===========================================================================

def generate_irrelevant_pdfs():
    print("\n=== Generating Irrelevant/Marketing PDF ===")

    make_text_pdf(
        PDF_DIR / "irrelevant" / "irr-01-marketing-flyer.pdf",
        "HealthTech Solutions - Special Offer",
        [
            ("MedBot Pro 3000", """
THE FUTURE OF HEALTHCARE MANAGEMENT IS HERE!

Introducing MedBot Pro 3000 - The World's Most Advanced
AI Healthcare Assistant!

ARE YOU READY TO TRANSFORM YOUR PRACTICE?
"""),
            ("What Our Customers Say", """
"I saved 50% on administrative costs!" - Dr. Smith, NYC
"Our efficiency increased by 200%!" - Nurse Johnson, LA
"Best investment we ever made!" - Hospital Admin, Chicago
"Patient satisfaction scores went through the roof!" - Dr. Lee
"""),
            ("Special Limited-Time Offer", """
Sign up before September 30, 2025 and receive:

50% OFF your first year (regular price $24,000/year)
FREE implementation (valued at $10,000)
FREE 24/7 premium support
FREE annual training workshop for your entire staff
FREE data migration from your current system

TOTAL SAVINGS: Over $30,000!
"""),
            ("Features", """
- Automated appointment scheduling
- AI-powered patient communication
- Real-time analytics dashboard
- Voice-to-text clinical notes
- Integration with 200+ EHR systems
- Mobile app for providers and patients
- Automated billing and coding assistance
- Patient portal with secure messaging
"""),
            ("Contact Us", """
DON'T MISS OUT! This offer expires soon!

Call now: 1-800-555-MEDS (6337)
Email: sales@healthtech-solutions.com
Web: www.healthtech-solutions.com/demo

Best regards,
The HealthTech Solutions Team

P.S. Remember, this offer is for a LIMITED TIME ONLY. Act now!

To unsubscribe: www.healthtech-solutions.com/unsubscribe
"""),
        ],
    )


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    print("=" * 60)
    print("SYNTHETIC TEST PDF GENERATOR")
    print("Smart Inbox Assistant Healthcare")
    print("=" * 60)
    print("\nALL DATA IS SYNTHETIC. No real patient information.")

    generate_digital_pdfs()
    generate_scanned_pdfs()
    generate_article_pdfs()
    generate_non_english_pdfs()
    generate_quality_complaint_pdfs()
    generate_info_request_pdfs()
    generate_irrelevant_pdfs()

    # Count generated PDFs
    pdf_count = len(list(PDF_DIR.rglob("*.pdf")))
    print(f"\n{'=' * 60}")
    print(f"GENERATION COMPLETE: {pdf_count} PDF files created")
    print(f"{'=' * 60}")

    # List all generated files
    print("\nGenerated files:")
    for pdf in sorted(PDF_DIR.rglob("*.pdf")):
        size = pdf.stat().st_size
        print(f"  {pdf.relative_to(SCRIPT_DIR)} ({size:,} bytes)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
