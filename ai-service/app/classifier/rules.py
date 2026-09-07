"""Rule-based multi-category classifier.

Business rules based on healthcare document classification assignment.
Each category is evaluated independently — a document can match multiple
categories with varying confidence.

When evidence is insufficient, confidence is lowered rather than guessing.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from .models import Category, CategoryResult, ClassificationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Keyword banks — grouped by category
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _KeywordRule:
    """A keyword/phrase with a weight contribution."""
    patterns: tuple[str, ...]
    weight: float  # contribution to confidence when matched


# SAFETY_REPORT: adverse events, incidents, patient harm, near-misses
# Includes French equivalents for non-English document support
_SAFETY_KEYWORDS: list[_KeywordRule] = [
    _KeywordRule(("adverse event", "adverse reaction", "side effect"), 0.35),
    _KeywordRule(("patient fall", "fell", "fallen"), 0.30),
    _KeywordRule(("medication error", "wrong medication", "wrong dose", "overdose"), 0.35),
    _KeywordRule(("near miss", "close call"), 0.25),
    _KeywordRule(("safety incident", "safety concern", "safety issue"), 0.30),
    _KeywordRule(("death", "fatal", "died", "deceased"), 0.40),
    _KeywordRule(("injury", "injured", "harm", "harmful"), 0.25),
    _KeywordRule(("allergic reaction", "anaphylaxis"), 0.30),
    _KeywordRule(("infection acquired", "hospital-acquired infection", "nosocomial"), 0.30),
    _KeywordRule(("device failure", "equipment malfunction"), 0.25),
    _KeywordRule(("sentinel event", "never event"), 0.40),
    _KeywordRule(("reportable", "mandatory report", "must report"), 0.20),
    _KeywordRule(("blood transfusion reaction", "transfusion error"), 0.30),
    _KeywordRule(("surgical error", "wrong site", "wrong patient"), 0.35),
    # French equivalents
    _KeywordRule(("evenement indeirable", "reaction indesirable", "effet secondaire"), 0.35),
    _KeywordRule(("chute du patient", "chute patient"), 0.30),
    _KeywordRule(("erreur medicament", "erreur de medication", "surdosage"), 0.35),
    _KeywordRule(("presqu'accident", "presqu-accident"), 0.25),
    _KeywordRule(("incident de securite", "probleme de securite"), 0.30),
    _KeywordRule(("deces", "decede", "mort", "deces"), 0.40),
    _KeywordRule(("blessure", "blesse", "prejudice", "nocif"), 0.25),
    _KeywordRule(("reaction allergique", "choc anaphylactique"), 0.30),
    _KeywordRule(("infection nosocomiale", "infection acquiree a l'hopital"), 0.30),
    _KeywordRule(("panne d'appareil", "dysfonctionnement"), 0.25),
    _KeywordRule(("evenement sentinelle", "evenement jamais du"), 0.40),
    _KeywordRule(("erreur chirurgicale", "mauvais site", "mauvais patient"), 0.35),
    _KeywordRule(("rapport", "signalement"), 0.15),
]

# QUALITY_COMPLAINT: dissatisfaction, service quality, complaints
# Includes French equivalents
_QUALITY_KEYWORDS: list[_KeywordRule] = [
    _KeywordRule(("complaint", "complain", "dissatisfied", "unhappy"), 0.30),
    _KeywordRule(("poor service", "bad service", "unacceptable service"), 0.30),
    _KeywordRule(("rude", "unprofessional", "disrespectful"), 0.25),
    _KeywordRule(("wait time", "waiting too long", "long wait", "waited", "delayed"), 0.20),
    _KeywordRule(("cleanliness", "dirty", "unclean", "hygiene"), 0.20),
    _KeywordRule(("noise", "noisy", "loud"), 0.15),
    _KeywordRule(("food quality", "meal quality", "bad food"), 0.20),
    _KeywordRule(("billing complaint", "overcharged", "wrong charge"), 0.25),
    _KeywordRule(("communication problem", "poor communication", "not informed"), 0.20),
    _KeywordRule(("discharged too early", "premature discharge"), 0.25),
    _KeywordRule(("follow-up", "no follow-up", "lost to follow-up"), 0.15),
    _KeywordRule(("unsatisfactory", "not satisfied", "poor quality", "unacceptable"), 0.25),
    _KeywordRule(("mistake", "error in care", "negligence"), 0.25),
    # French equivalents
    _KeywordRule(("plainte", "reclamation", "insatisfait", "mécontent"), 0.30),
    _KeywordRule(("mauvais service", "service inacceptable"), 0.30),
    _KeywordRule(("impoli", "professionnel", "irrespectueux"), 0.25),
    _KeywordRule(("temps d'attente", "attente trop longue", "retard"), 0.20),
    _KeywordRule(("proprete", "sale", "hygiene"), 0.20),
    _KeywordRule(("bruit", "bruyant", "fort"), 0.15),
    _KeywordRule(("qualite des repas", "mauvaise nourriture"), 0.20),
    _KeywordRule(("facturation", "surfacturation", "erreur de facturation"), 0.25),
    _KeywordRule(("probleme de communication", "mauvaise communication"), 0.20),
    _KeywordRule(("sortie anticipee", "decharge prematuree"), 0.25),
    _KeywordRule(("suivi", "pas de suivi"), 0.15),
    _KeywordRule(("insatisfaisant", "non satisfait", "mauvaise qualite"), 0.25),
    _KeywordRule(("erreur de soin", "negligence"), 0.25),
]

# INFO_REQUEST: questions, requests for information, inquiries
# Includes French equivalents
_INFO_KEYWORDS: list[_KeywordRule] = [
    _KeywordRule(("question", "inquiry", "request for information"), 0.30),
    _KeywordRule(("could you", "can you", "would you", "please provide"), 0.25),
    _KeywordRule(("what is", "what are", "how do", "how is"), 0.20),
    _KeywordRule(("need information", "need details", "need clarification"), 0.30),
    _KeywordRule(("status update", "update on", "progress report"), 0.25),
    _KeywordRule(("schedule", "appointment", "availability"), 0.15),
    _KeywordRule(("results", "test results", "lab results"), 0.20),
    _KeywordRule(("copies", "copy of", "records request"), 0.20),
    _KeywordRule(("referral", "refer", "transfer"), 0.15),
    _KeywordRule(("?",), 0.10),  # question marks indicate inquiry
    # French equivalents
    _KeywordRule(("question", "demande d'information", "requete"), 0.30),
    _KeywordRule(("pourriez-vous", "pouvez-vous", "voudriez-vous", "fournir"), 0.25),
    _KeywordRule(("quel est", "quelle est", "comment", "pourquoi"), 0.20),
    _KeywordRule(("besoin d'information", "besoin de precisions", "besoin de clarification"), 0.30),
    _KeywordRule(("mise a jour", "etat d'avancement", "rapport d'avancement"), 0.25),
    _KeywordRule(("rendez-vous", "disponibilite", "planning"), 0.15),
    _KeywordRule(("resultats", "resultats de test", "resultats de laboratoire"), 0.20),
    _KeywordRule(("copies", "copie de", "demande de dossier"), 0.20),
    _KeywordRule(("orientation", " transfert"), 0.15),
]

# NOT_RELEVANT: spam, marketing, personal, unrelated
_IRRELEVANT_KEYWORDS: list[_KeywordRule] = [
    _KeywordRule(("spam", "unsubscribe", "opt out"), 0.30),
    _KeywordRule(("marketing", "promotion", "advertisement", "sale"), 0.25),
    _KeywordRule(("newsletter", "digest", "weekly update"), 0.15),
    _KeywordRule(("congratulations", "winner", "prize", "lottery"), 0.30),
    _KeywordRule(("viagra", "cialis", "pharmacy", "discount medication"), 0.35),
    _KeywordRule(("dear friend", "dear valued", "dear customer"), 0.15),
    _KeywordRule(("click here", "visit our", "buy now"), 0.20),
    _KeywordRule(("survey", "feedback request", "rate us"), 0.10),
]

# ---------------------------------------------------------------------------
# Category-specific context phrases (boost confidence when present)
# ---------------------------------------------------------------------------

_SAFETY_CONTEXT = (
    "incident report", "reportable event", "patient safety",
    "risk management", "quality improvement", "root cause",
)


# ---------------------------------------------------------------------------
# Classification engine
# ---------------------------------------------------------------------------

_MIN_CONFIDENCE_THRESHOLD = 0.05  # Below this, category is dropped


def _count_pattern_matches(text_lower: str, patterns: tuple[str, ...]) -> int:
    """Count how many times any pattern in the tuple appears in text."""
    return sum(1 for p in patterns if p in text_lower)


def _score_category(
    text_lower: str,
    keyword_rules: list[_KeywordRule],
    context_phrases: tuple[str, ...] | None = None,
) -> tuple[float, list[str]]:
    """Score a single category against the text.

    Returns (confidence, list_of_reasons).
    """
    total_weight = 0.0
    reasons: list[str] = []

    for rule in keyword_rules:
        matches = _count_pattern_matches(text_lower, rule.patterns)
        if matches > 0:
            total_weight += rule.weight * min(matches, 3)  # cap at 3x per rule
            matched = [p for p in rule.patterns if p in text_lower]
            reasons.append(f"Matched: {', '.join(matched[:2])}")

    # Context boost
    if context_phrases:
        ctx_matches = sum(1 for cp in context_phrases if cp in text_lower)
        if ctx_matches > 0:
            total_weight += 0.10 * min(ctx_matches, 3)
            reasons.append(f"Context phrases present ({ctx_matches})")

    # Cap confidence at 0.99 and floor at 0
    confidence = min(max(total_weight, 0.0), 0.99)

    # Penalise if text is very short (insufficient information) — only when keywords matched
    if confidence > 0:
        word_count = len(text_lower.split())
        if word_count < 5:
            confidence *= 0.3
            reasons.append("Very short text — low information density")
        elif word_count < 15:
            confidence *= 0.7
            reasons.append("Short text — limited information")

    return round(confidence, 4), reasons


def classify(text: str) -> ClassificationResult:
    """Classify text into one or more categories.

    Each category is evaluated independently.  Categories with confidence
    below the threshold are excluded.  Results are sorted by confidence
    descending.
    """
    if not text or not text.strip():
        return ClassificationResult(
            categories=[
                CategoryResult(
                    category=Category.NOT_RELEVANT,
                    confidence=0.95,
                    reason="Empty or blank document — no content to classify",
                )
            ]
        )

    lower = text.lower()

    # Score each category independently
    scored: list[CategoryResult] = []

    # SAFETY_REPORT
    conf, reasons = _score_category(lower, _SAFETY_KEYWORDS, _SAFETY_CONTEXT)
    if conf >= _MIN_CONFIDENCE_THRESHOLD and reasons:
        scored.append(CategoryResult(
            category=Category.SAFETY_REPORT,
            confidence=conf,
            reason=reasons[0] if reasons else "No strong safety signals",
        ))

    # QUALITY_COMPLAINT
    conf, reasons = _score_category(lower, _QUALITY_KEYWORDS)
    if conf >= _MIN_CONFIDENCE_THRESHOLD and reasons:
        scored.append(CategoryResult(
            category=Category.QUALITY_COMPLAINT,
            confidence=conf,
            reason=reasons[0] if reasons else "No strong quality signals",
        ))

    # INFO_REQUEST
    conf, reasons = _score_category(lower, _INFO_KEYWORDS)
    if conf >= _MIN_CONFIDENCE_THRESHOLD and reasons:
        scored.append(CategoryResult(
            category=Category.INFO_REQUEST,
            confidence=conf,
            reason=reasons[0] if reasons else "No strong inquiry signals",
        ))

    # NOT_RELEVANT
    conf, reasons = _score_category(lower, _IRRELEVANT_KEYWORDS)
    if conf >= _MIN_CONFIDENCE_THRESHOLD and reasons:
        scored.append(CategoryResult(
            category=Category.NOT_RELEVANT,
            confidence=conf,
            reason=reasons[0] if reasons else "No relevance signals",
        ))

    # If nothing matched, default to NOT_RELEVANT with low confidence
    if not scored:
        scored.append(CategoryResult(
            category=Category.NOT_RELEVANT,
            confidence=0.30,
            reason="No category matched with sufficient confidence",
        ))

    # Sort by confidence descending
    scored.sort(key=lambda c: c.confidence, reverse=True)

    logger.info(
        "Classified into %d categories: %s",
        len(scored),
        ", ".join(f"{c.category.value}={c.confidence:.2f}" for c in scored),
    )

    return ClassificationResult(categories=scored)
