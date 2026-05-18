"""
apps/fraud_detection/document_analyzer.py

Evidence document analyser — does NOT use Claude or any external API.
Uses rule-based heuristics keyed to the actual Claim model field values.

To plug in your own ML model, replace the body of
analyze_document_legitimacy() while keeping the same return signature:
    (legitimacy_score: float, flags: List[str])
"""

import os
import re
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_document_text(evidence_file) -> str | None:
    """
    Extract plain text from an uploaded evidence file.

    Supported formats
    ─────────────────
    Images (.jpg .jpeg .png .webp .bmp) → pytesseract OCR
    PDFs   (.pdf)                        → pypdf text layer

    Returns the extracted string, or None on failure / unsupported format.
    """
    try:
        file_path = evidence_file.path
        ext       = os.path.splitext(file_path)[1].lower()

        if ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            return _ocr_image(file_path)
        if ext == ".pdf":
            return _extract_pdf(file_path)

        logger.warning("Unsupported evidence format: %s", ext)
        return None

    except Exception:
        logger.exception("Document text extraction failed")
        return None


def _ocr_image(file_path: str) -> str | None:
    try:
        import pytesseract
        from PIL import Image
        text = pytesseract.image_to_string(Image.open(file_path))
        return text.strip() or None
    except ImportError:
        logger.error("pytesseract / Pillow missing — run: pip install pytesseract pillow")
        return None
    except Exception:
        logger.exception("OCR failed for %s", file_path)
        return None


def _extract_pdf(file_path: str) -> str | None:
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        text   = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        return text or None
    except ImportError:
        logger.error("pypdf missing — run: pip install pypdf")
        return None
    except Exception:
        logger.exception("PDF extraction failed for %s", file_path)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

# ── Claim.claim_type choices: ACCIDENT THEFT VANDALISM NATURAL_DISASTER FIRE OTHER
_CLAIM_TYPE_KEYWORDS: dict[str, list[str]] = {
    "ACCIDENT":        ["collision", "crash", "impact", "accident", "vehicle", "driver"],
    "THEFT":           ["stolen", "theft", "burglar", "missing", "break-in", "took"],
    "VANDALISM":       ["vandal", "graffiti", "smashed", "damaged", "keyed", "defaced"],
    "NATURAL_DISASTER":["flood", "storm", "hail", "hurricane", "tornado", "earthquake", "lightning"],
    "FIRE":            ["fire", "burn", "smoke", "flame", "arson", "blaze"],
    "OTHER":           [],
}

# ── Claim.severity choices: MINOR MODERATE MAJOR TOTAL_LOSS
_SEVERITY_AMOUNT_BANDS: dict[str, tuple[float, float]] = {
    "MINOR":      (0,       5_000),
    "MODERATE":   (500,    25_000),
    "MAJOR":      (5_000, 120_000),
    "TOTAL_LOSS": (8_000, 999_999),
}

_OFFICIAL_KEYWORDS = [
    "case number", "case no", "reference number", "report number",
    "badge", "officer", "constable", "detective", "sergeant",
    "police station", "department", "authority",
    "incident report", "official report", "certified",
]

_SUSPICIOUS_PHRASES = [
    "i cannot remember", "i don't recall", "not sure about",
    "roughly", "about that time",
    "i was alone", "no witnesses", "no cameras",
    "cash settlement", "do not contact insurance",
]


def analyze_document_legitimacy(
    document_text: str | None,
    claim,                          # Claim model instance
) -> Tuple[float, List[str]]:
    """
    Score how legitimate the uploaded evidence document appears.

    Returns
    ───────
    legitimacy_score : float in [0.0, 1.0]
        1.0 = clearly legitimate    0.0 = strong fraud indicators
    flags : List[str]
        Human-readable reasons behind the score (stored on the claim).

    ┌──────────────────────────────────────────────────────────────────┐
    │  PLUG IN YOUR OWN ML MODEL HERE                                  │
    │  Replace the function body below with calls to your model while  │
    │  keeping the same return type: Tuple[float, List[str]].          │
    │                                                                  │
    │  Example skeleton:                                               │
    │    feats = build_features(document_text, claim)                 │
    │    score = my_classifier.predict_proba(feats)[0][1]             │
    │    return float(score), []                                       │
    └──────────────────────────────────────────────────────────────────┘
    """
    flags: List[str] = []

    # ── guard: no usable text ─────────────────────────────────────────────
    if not document_text or len(document_text.strip()) < 50:
        flags.append("Document is empty, unreadable, or too short to analyse.")
        return 0.35, flags

    text_lower  = document_text.lower()
    score       = 0.50                  # neutral baseline

    # ── 1. Official markers (+0.05 each, capped at +0.20) ────────────────
    official_hits = sum(1 for kw in _OFFICIAL_KEYWORDS if kw in text_lower)
    if official_hits:
        score += min(official_hits * 0.05, 0.20)
    else:
        flags.append("No official reference numbers or officer details found.")
        score -= 0.10

    # ── 2. Suspicious language (-0.08 each, capped at -0.24) ─────────────
    suspicious_hits = [ph for ph in _SUSPICIOUS_PHRASES if ph in text_lower]
    if suspicious_hits:
        score -= min(len(suspicious_hits) * 0.08, 0.24)
        flags.append(
            "Suspicious language detected: "
            + "; ".join(suspicious_hits[:3])
        )

    # ── 3. Claim-type keyword consistency ────────────────────────────────
    expected_kws = _CLAIM_TYPE_KEYWORDS.get(claim.claim_type, [])
    if expected_kws:
        hits = sum(1 for kw in expected_kws if kw in text_lower)
        if hits == 0:
            flags.append(
                f"Document language does not match claim type '{claim.claim_type}'."
            )
            score -= 0.12
        elif hits >= 3:
            score += 0.08

    # ── 4. Claimed amount vs. severity band ──────────────────────────────
    if claim.claimed_amount and claim.severity:
        low, high = _SEVERITY_AMOUNT_BANDS.get(claim.severity, (0, 999_999))
        amount    = float(claim.claimed_amount)
        if amount < low:
            flags.append(
                f"Claimed amount ${amount:,.0f} is unusually low for "
                f"{claim.severity} severity."
            )
            score -= 0.05
        elif amount > high * 1.5:
            flags.append(
                f"Claimed amount ${amount:,.0f} greatly exceeds the typical "
                f"{claim.severity} range."
            )
            score -= 0.10

    # ── 5. Incident date mentioned ────────────────────────────────────────
    if claim.incident_date:
        # tz-aware datetimes need .date() first
        inc = claim.incident_date
        day_str   = str(inc.day)
        month_str = inc.strftime("%B").lower()   # e.g. "january"
        year_str  = str(inc.year)

        if not (day_str in document_text or month_str in text_lower or year_str in document_text):
            flags.append("Incident date not referenced in the document.")
            score -= 0.08

    # ── 6. Incident location mentioned ───────────────────────────────────
    if claim.incident_location:
        loc_words   = [w for w in claim.incident_location.lower().split() if len(w) > 3]
        loc_matches = sum(1 for w in loc_words if w in text_lower)
        if loc_words and loc_matches == 0:
            flags.append("Incident location not referenced in the document.")
            score -= 0.07

    # ── 7. Document length ────────────────────────────────────────────────
    word_count = len(document_text.split())
    if word_count < 80:
        flags.append(f"Document is very brief ({word_count} words).")
        score -= 0.06
    elif word_count > 300:
        score += 0.05           # detailed report is a positive signal

    # ── clamp ─────────────────────────────────────────────────────────────
    legitimacy_score = round(min(max(score, 0.0), 1.0), 4)

    if not flags:
        flags.append("No specific document legitimacy concerns detected.")

    return legitimacy_score, flags


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE COMBINER  (used by signals.py)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_combined_fraud_score(
    ml_fraud_score:    float,
    document_legitimacy: float,
    ml_weight:  float = 0.65,
    doc_weight: float = 0.35,
) -> float:
    """
    Blend ML fraud probability with document illegitimacy into one score.

    ml_fraud_score      : 0 = legitimate,  1 = fraudulent
    document_legitimacy : 0 = suspicious,  1 = clearly legitimate
    → (1 - legitimacy) converts document score to the same fraud direction.
    """
    doc_fraud = 1.0 - document_legitimacy
    combined  = ml_weight * ml_fraud_score + doc_weight * doc_fraud
    return round(min(max(combined, 0.0), 1.0), 4)