import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.fault import Fault

MINIMUM_MATCH_SCORE = 20

STOP_WORDS = {
    "en": {
        "my", "the", "a", "an", "is", "are", "was", "were",
        "and", "or", "but", "with", "for", "to", "of", "in",
        "on", "at", "it", "this", "that", "has", "have",
        "been", "very", "please", "when", "i", "am",
        "phone", "laptop", "router",
    },
    "sw": {
        "na", "ya", "wa", "za", "kwa", "ni", "sana",
        "hii", "hiyo", "kwenye", "lakini", "au", "imekuwa",
        "simu", "kompyuta", "router", "yangu", "zangu",
        "ina", "inafanya", "tafadhali",
    },
}


def normalize_text(value: str) -> str:
    """Normalize text for consistent keyword comparison."""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def extract_tokens(value: str, language: str) -> set[str]:
    """Extract meaningful words from symptom or keyword text."""
    normalized = normalize_text(value)
    stop_words = STOP_WORDS.get(language, STOP_WORDS["en"])
    return {
        word for word in normalized.split()
        if word and word not in stop_words
    }


def calculate_match_score(
    symptom: str | set[str],
    keywords: list[str] | Fault,
    language: str = "en",
) -> int:
    """
    Calculate a heuristic match score (0-100) between symptom and fault keywords.

    Calculates keyword overlap using token precision, recall, and harmonic mean (F1).
    """
    if isinstance(symptom, (set, list, tuple)):
        symptom_tokens = set(symptom)
        symptom_text = " ".join(symptom)
    else:
        symptom_text = str(symptom)
        symptom_tokens = extract_tokens(symptom_text, language)

    if not symptom_tokens:
        return 0

    if isinstance(keywords, Fault):
        kw_list = keywords.keywords_sw if language == "sw" else keywords.keywords_en
    elif isinstance(keywords, str):
        kw_list = [keywords]
    elif isinstance(keywords, (list, tuple, set)):
        kw_list = list(keywords)
    else:
        kw_list = []

    if not kw_list:
        return 0

    best_score = 0.0
    norm_symptom = normalize_text(symptom_text)

    for phrase in kw_list:
        phrase_tokens = extract_tokens(phrase, language)
        if not phrase_tokens:
            continue

        common = symptom_tokens & phrase_tokens
        if not common:
            continue

        recall = len(common) / len(phrase_tokens)
        precision = len(common) / len(symptom_tokens)

        # Single-token match against a longer phrase represents weak evidence
        if len(common) < 2 and len(phrase_tokens) >= 3:
            score = recall * precision
        else:
            score = (2.0 * precision * recall) / (precision + recall)

        norm_phrase = normalize_text(phrase)
        if norm_phrase and norm_phrase in norm_symptom:
            score = max(score, recall)

        if score > best_score:
            best_score = score

    return min(100, max(0, int(round(best_score * 100))))


def diagnose(
    db: Session,
    device_slug: str | None = None,
    symptom: str = "",
    language: str = "en",
    device: str | None = None,
) -> tuple[Device | None, list[dict]]:
    """
    Diagnose possible hardware faults for a device given a symptom description.

    Compares the symptom against seeded fault records using keyword overlap,
    filters by MINIMUM_MATCH_SCORE, and returns up to 3 ranked matches.
    """
    slug = device_slug if device_slug is not None else device
    if not slug:
        return None, []

    normalized_device = normalize_text(slug)
    device_obj = db.scalar(
        select(Device).where(
            (Device.slug == normalized_device) | (Device.name.ilike(normalized_device))
        )
    )
    if device_obj is None:
        return None, []

    if not symptom or not symptom.strip():
        return device_obj, []

    faults = db.scalars(
        select(Fault).where(Fault.device_id == device_obj.id)
    ).all()

    lang = language.lower() if language else "en"
    if lang not in STOP_WORDS:
        lang = "en"

    candidates = []
    for fault in faults:
        score = calculate_match_score(symptom, fault, language=lang)
        if score >= MINIMUM_MATCH_SCORE:
            candidates.append({
                "fault": fault.fault_name,
                "match_score": score,
                "risk_level": fault.risk_level,
                "estimated_cost": {
                    "min": fault.cost_min,
                    "max": fault.cost_max,
                    "currency": "KES",
                },
                "fix_steps": fault.fix_steps,
            })

    # Rank by match_score descending, then cost_min ascending
    candidates.sort(key=lambda item: (-item["match_score"], item["estimated_cost"]["min"]))

    return device_obj, candidates[:3]
