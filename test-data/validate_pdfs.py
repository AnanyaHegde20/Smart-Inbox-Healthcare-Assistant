#!/usr/bin/env python3
"""Validate generated test PDFs and emails."""
import fitz
from pathlib import Path

PDF_DIR = Path("test-data/pdfs")
SCRIPT_DIR = Path("test-data")

print("=== PDF VALIDATION ===")

# Count all PDFs
all_pdfs = list(PDF_DIR.rglob("*.pdf"))
print(f"\nTotal PDF files: {len(all_pdfs)}")

# Count by category
categories = {}
for pdf in all_pdfs:
    rel = pdf.relative_to(PDF_DIR)
    cat = rel.parts[0]
    categories.setdefault(cat, []).append(pdf)

for cat, files in sorted(categories.items()):
    print(f"  {cat}: {len(files)}")
    for f in files:
        print(f"    - {f.name}")

# Check digital PDFs have extractable text
print("\n--- Digital PDF text extraction ---")
for pdf in sorted((PDF_DIR / "digital").glob("*.pdf")):
    doc = fitz.open(str(pdf))
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    has_text = len(text.strip()) > 50
    print(f"  {pdf.name}: text={len(text.strip())} chars, extractable={has_text}")

# Check scanned PDFs are image-based
print("\n--- Scanned PDF image verification ---")
for pdf in sorted((PDF_DIR / "scanned").glob("*.pdf")):
    doc = fitz.open(str(pdf))
    has_images = False
    has_text = False
    for page in doc:
        imgs = page.get_images()
        text = page.get_text().strip()
        if imgs:
            has_images = True
        if text:
            has_text = True
    doc.close()
    print(f"  {pdf.name}: images={has_images}, selectable_text={has_text}")

# Check non-English PDFs
print("\n--- Non-English PDF content ---")
for pdf in sorted((PDF_DIR / "non-english").glob("*.pdf")):
    doc = fitz.open(str(pdf))
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    has_non_ascii = any(ord(c) > 127 for c in text)
    print(f"  {pdf.name}: text_len={len(text.strip())}, has_non_ascii={has_non_ascii}")

# Check articles
print("\n--- Article PDFs ---")
for pdf in sorted((PDF_DIR / "articles").glob("*.pdf")):
    doc = fitz.open(str(pdf))
    text = "".join(page.get_text() for page in doc)
    doc.close()
    print(f"  {pdf.name}: {len(text.strip())} chars")

# Check quality complaints
print("\n--- Quality Complaint PDFs ---")
for pdf in sorted((PDF_DIR / "quality-complaints").glob("*.pdf")):
    doc = fitz.open(str(pdf))
    text = "".join(page.get_text() for page in doc)
    doc.close()
    print(f"  {pdf.name}: {len(text.strip())} chars")

# Check info requests
print("\n--- Info Request PDFs ---")
for pdf in sorted((PDF_DIR / "info-requests").glob("*.pdf")):
    doc = fitz.open(str(pdf))
    text = "".join(page.get_text() for page in doc)
    doc.close()
    print(f"  {pdf.name}: {len(text.strip())} chars")

# Check irrelevant
print("\n--- Irrelevant PDF ---")
for pdf in sorted((PDF_DIR / "irrelevant").glob("*.pdf")):
    doc = fitz.open(str(pdf))
    text = "".join(page.get_text() for page in doc)
    doc.close()
    print(f"  {pdf.name}: {len(text.strip())} chars")

# Count reaction emails
print("\n--- Reaction-Focused Emails ---")
email_dir = SCRIPT_DIR / "emails"
reaction_emails = list(email_dir.glob("email-1[1-4]-reaction-*.txt"))
for e in sorted(reaction_emails):
    content = e.read_text()
    lines = content.strip().split("\n")
    subj = [l for l in lines if l.startswith("Subject:")]
    print(f"  {e.name}: {len(lines)} lines, {subj[0] if subj else '?'}")

# All emails count
all_emails = list(email_dir.glob("email-*.txt"))
print(f"\nTotal emails: {len(all_emails)}")

print("\n=== VALIDATION COMPLETE ===")
