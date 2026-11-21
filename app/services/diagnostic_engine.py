import re
import unicodedata
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.fault import Fault

MINIMUM_MATCH_SCORE = 20
MAXIMUM_MATCH_SCORE = 95

# Stop words in English and Swahili
STOP_WORDS = {
    "en": {
        "my", "the", "a", "an", "is", "are", "was", "were",
        "and", "or", "but", "with", "for", "to", "of", "in",
        "on", "at", "it", "this", "that", "has", "have", "had",
        "do", "does", "did",
        "been", "very", "please", "when", "i", "am",
        "phone", "laptop", "router", "device", "some",
    },
    "sw": {
        "na", "ya", "wa", "za", "kwa", "ni", "sana",
        "hii", "hiyo", "kwenye", "lakini", "au", "imekuwa",
        "simu", "kompyuta", "router", "yangu", "zangu",
        "ina", "inafanya", "tafadhali", "kifaa",
    },
}

# Negation terms across English and Swahili
NEGATION_TERMS = {
    "not", "no", "never", "doesnt", "does not", "didnt", "did not",
    "wont", "will not", "cannot", "cant", "isnt", "is not", "without",
    "dont", "do not", "wasnt", "arent",
    "siyo", "bila", "hapana", "si", "haitaki",
}

# Stems of defect/fault words whose negation indicates absence of defect
DEFECT_STEMS = {
    "break", "broken", "crack", "pasuk", "vunj", "drain", "chemk",
    "heat", "hot", "overheat", "zim", "slow", "freez", "gand",
    "stuck", "loos", "click", "damage", "poor", "bad", "dhaifu", "harib",
}

# Bilingual synonyms and technical domain concept clusters
SYNONYM_CLUSTERS = {
    "screen": {"screen", "display", "kioo", "skrini", "monitor", "panel", "lcd", "oled"},
    "battery": {"battery", "betri", "power", "chaji", "charge", "charging", "charger", "chargers", "kuchaji"},
    "broken": {
        "broken", "cracked", "shattered", "imepasuka", "imevunjika",
        "imecrack", "damaged", "crack", "pasuka", "vunjika", "vunja", "cracks",
    },
    "heat": {"heat", "hot", "overheating", "inachemka", "joto", "warm", "overheat", "chemka"},
    "black": {"black", "blank", "nyeusi", "giza", "dark", "off"},
    "reboot": {"restart", "reboot", "inajiwasha", "inajizima", "bootloop", "loop", "washa", "zima"},
    "water": {"water", "liquid", "maji", "wet", "mvua", "liquids", "lowa", "imelowa", "kumwagiwa"},
    "slow": {"slow", "lagging", "hanging", "inaganda", "polepole", "freeze", "freezing", "ganda"},
    "sound": {"audio", "sound", "speaker", "sauti", "mic", "microphone", "earpiece"},
    "wifi": {"wifi", "wi-fi", "wireless", "hotspot", "wlan"},
    "network": {"internet", "network", "mtandao", "online", "data"},
    "dns": {"dns", "nxdomain", "nameserver", "resolve", "resolution"},
    "web": {"websites", "website", "web", "tovuti", "site", "sites", "domain", "url", "page", "pages"},
    "open": {"open", "load", "loading", "funguka", "fungua", "funguki", "access"},
    "port": {"port", "jack", "sehemu", "plagi", "plug", "socket"},
    "keyboard": {"keyboard", "keys", "key", "vibonyezo", "herufi", "typing", "type"},
    "button": {"button", "switch", "kitufe", "vitendo", "power button", "volume"},
    "camera": {"camera", "kamera", "picha", "lens"},
    "storage": {"ssd", "hdd", "disk", "drive", "hard drive", "storage", "hifadhi"},
    "boot": {"boot", "bootable", "booting", "startup"},
    "weak": {"weak", "dhaifu", "low", "poor", "chache", "short"},
    "coverage": {"signal", "bars", "range", "coverage", "distance", "far", "mbali", "chumba"},
    "disconnect": {"disconnect", "disconnections", "drops", "katika", "drop"},
}

SYNONYM_MAP = {
    word: canonical
    for canonical, words in SYNONYM_CLUSTERS.items()
    for word in words
}

FOLLOW_UP_RULES = [
    {
        "device": "laptop",
        "faults": {"RAM fault", "Display panel failure", "Display cable fault", "Motherboard or power circuit fault"},
        "trigger_keywords": {"black", "screen", "nyeusi", "display"},
        "question": "Does the laptop display anything when connected to an external monitor or TV via HDMI?",
        "options": [
            {"label": "Yes, external monitor displays picture", "indicates": "Display panel failure"},
            {"label": "No, external monitor is also black", "indicates": "RAM fault"},
            {"label": "I haven't tested with an external monitor", "indicates": None},
        ],
    },
    {
        "device": "phone",
        "faults": {"Charging port damage", "Battery degradation", "Charging accessory fault", "Mainboard or power-management fault"},
        "trigger_keywords": {"charge", "charging", "chaji", "battery", "betri"},
        "question": "Does the phone charge or react when plugged in using a different, known-good cable and adapter?",
        "options": [
            {"label": "Yes, it charges fine with another charger", "indicates": "Charging accessory fault"},
            {"label": "No, it still does not charge or only charges at an angle", "indicates": "Charging port damage"},
            {"label": "It charges, but the battery drops quickly once unplugged", "indicates": "Battery degradation"},
        ],
    },
    {
        "device": "phone",
        "faults": {"Broken display panel", "Touchscreen digitizer failure"},
        "trigger_keywords": {"screen", "touch", "kioo", "display", "cracked", "pasuka"},
        "question": "Is the screen glass physically cracked or showing black ink spots, or is only the touch responsiveness failing?",
        "options": [
            {"label": "Glass or screen has visible cracks or black spots", "indicates": "Broken display panel"},
            {"label": "Glass is smooth and undamaged, but touches are erratic or unresponsive", "indicates": "Touchscreen digitizer failure"},
        ],
    },
    {
        "device": "router",
        "faults": {"ISP service outage", "WAN cable or port fault", "DNS resolution failure", "Power adapter failure"},
        "trigger_keywords": {"internet", "wifi", "network", "mtandao", "outage"},
        "question": "What is the status of the Internet / WAN indicator LED on the front of your router?",
        "options": [
            {"label": "Red, orange, or completely off", "indicates": "WAN cable or port fault"},
            {"label": "Solid green or white, but websites fail to load", "indicates": "DNS resolution failure"},
            {"label": "All router lights are off or repeatedly power cycling", "indicates": "Power adapter failure"},
        ],
    },
    {
        "device": "laptop",
        "faults": {"Cooling fan failure", "Dust-clogged cooling system", "Motherboard or power circuit fault"},
        "trigger_keywords": {"heat", "hot", "overheating", "chemka", "feni", "fan"},
        "question": "Can you hear or feel the cooling fan spinning when the laptop starts heating up?",
        "options": [
            {"label": "Fan is spinning loudly with very hot exhaust air", "indicates": "Dust-clogged cooling system"},
            {"label": "Fan remains completely silent and does not spin", "indicates": "Cooling fan failure"},
            {"label": "Laptop shuts off suddenly under load without warning", "indicates": "Motherboard or power circuit fault"},
        ],
    },
]


def normalize_text(value: str) -> str:
    """Normalize text for consistent keyword comparison."""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )
    value = value.lower()
    value = re.sub(r"\bwi\s*[-_]?\s*fi\b", "wifi", value)
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def strip_swahili_prefixes(word: str) -> str:
    """Strip common Swahili/Sheng inflectional prefixes to get base root."""
    for pfx in ("ime", "ina", "kime", "vina", "ku", "ali", "ili", "wana", "wame"):
        if word.startswith(pfx) and len(word) > len(pfx) + 2:
            return word[len(pfx):]
    for pfx in ("hai", "hazi", "hawa", "haku", "haja"):
        if word.startswith(pfx) and len(word) > len(pfx) + 2:
            return word[len(pfx):]
    return word


def extract_tokens(value: str, language: str = "en") -> set[str]:
    """Extract meaningful words from text, applying stop words and canonical synonyms."""
    normalized = normalize_text(value)
    stop_words = STOP_WORDS.get(language, STOP_WORDS["en"])
    tokens: set[str] = set()

    for word in normalized.split():
        if not word or word in stop_words or word in NEGATION_TERMS:
            continue

        tokens.add(word)
        if word.startswith("charg"):
            tokens.add("charge")
        canonical = SYNONYM_MAP.get(word)
        if canonical:
            tokens.add(canonical)

        root = strip_swahili_prefixes(word)
        if root != word and root not in stop_words and len(root) >= 3:
            tokens.add(root)
            canonical_root = SYNONYM_MAP.get(root)
            if canonical_root:
                tokens.add(canonical_root)

    return tokens


def has_negation(text: str) -> bool:
    """Check if a phrase or clause contains a negation term."""
    norm = normalize_text(text)
    words = norm.split()
    for w in words:
        if w in NEGATION_TERMS:
            return True
        if w.startswith(("hai", "hazi", "haku")) and len(w) >= 5:
            return True
    return False


def is_defect_negated(text: str) -> bool:
    """Check if a clause specifically negates a defect keyword."""
    words = text.lower().split()
    for i, w in enumerate(words):
        w_clean = re.sub(r"[^a-z0-9]", "", w)
        is_neg = (
            w_clean in NEGATION_TERMS
            or w_clean in {"not", "no", "never", "doesnt", "didnt", "isnt", "siyo", "bila", "haitaki"}
            or w_clean.startswith(("hai", "hazi", "hawa", "haku"))
        )
        if is_neg:
            for following in words[i:]:
                following_clean = re.sub(r"[^a-z0-9]", "", following)
                following_root = re.sub(r"^(?:hai|hazi|hawa|haku|ha|ime|ina)", "", following_clean)
                if any(following_root.startswith(ds) for ds in DEFECT_STEMS):
                    return True
    return False


def split_into_clauses(text: str) -> list[tuple[str, bool]]:
    """
    Split symptom text into clauses, marking each clause as defect-negated or affirmative.
    Handles contrast conjunctions (but, lakini, although, etc.) and punctuation.
    """
    raw_clauses = re.split(
        r"[,;]|\b(?:but|lakini|although|though|however|hata hivyo|wala|isipokuwa)\b",
        text,
        flags=re.IGNORECASE,
    )
    result = []
    for raw in raw_clauses:
        part = raw.strip()
        if part:
            result.append((part, is_defect_negated(part)))
    return result or [(text, is_defect_negated(text))]


def calculate_match_score(
    symptom: str | set[str],
    keywords: list[str] | Fault,
    language: str = "en",
) -> int:
    """
    Calculate a heuristic match score (0-95) between symptom and fault keywords.

    Incorporates:
    - Negation detection: contradicts faults that match negated defect clauses
    - Synonym clustering & Swahili code-switching
    - Exact phrase match bonus
    - Precision/recall harmonic mean (F1)
    - Capping at 95 maximum score
    """
    if isinstance(symptom, (set, list, tuple)):
        symptom_text = " ".join(symptom)
    else:
        symptom_text = str(symptom)

    if not symptom_text.strip():
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

    clauses = split_into_clauses(symptom_text)
    affirmative_clauses = [part for part, is_neg in clauses if not is_neg]
    negated_clauses = [part for part, is_neg in clauses if is_neg]

    affirmative_text = " ".join(affirmative_clauses).strip()
    affirmative_tokens = extract_tokens(affirmative_text, language) if affirmative_text else set()
    norm_affirmative = normalize_text(affirmative_text) if affirmative_text else ""

    best_affirmative = 0.0
    best_negated = 0.0

    for phrase in kw_list:
        phrase_tokens = extract_tokens(phrase, language)
        if not phrase_tokens:
            continue

        norm_phrase = normalize_text(phrase)

        # 1. Check if phrase matches any defect-negated clause
        for neg_clause in negated_clauses:
            neg_tokens = extract_tokens(neg_clause, language)
            neg_common = neg_tokens & phrase_tokens
            if neg_common:
                neg_recall = len(neg_common) / len(phrase_tokens)
                if len(neg_common) >= 2 or len(phrase_tokens) == 1:
                    if neg_recall > best_negated:
                        best_negated = neg_recall

        # 2. Check if phrase matches affirmative symptom
        if affirmative_tokens:
            common = affirmative_tokens & phrase_tokens
            if common:
                recall = len(common) / len(phrase_tokens)
                precision = len(common) / len(affirmative_tokens)

                if norm_phrase and norm_phrase in norm_affirmative:
                    score = 0.95
                elif phrase_tokens.issubset(affirmative_tokens) and len(phrase_tokens) >= 2:
                    score = 0.95
                elif len(common) < 2 and len(phrase_tokens) >= 3:
                    score = recall * precision
                else:
                    score = (2.0 * precision * recall) / (precision + recall)
                    if recall >= 0.65:
                        score = max(score, recall * 0.95)

                if score > best_affirmative:
                    best_affirmative = score

    # If the fault only matches a negated defect clause without affirmative support, reject it
    if best_affirmative == 0.0 and best_negated > 0.0:
        return 0

    if best_negated >= 0.5 and best_affirmative < 0.8:
        return 0

    score_pct = int(round(best_affirmative * 100))
    return min(MAXIMUM_MATCH_SCORE, max(0, score_pct))


def get_safety_details(fault: Fault) -> tuple[str, bool]:
    """Return appropriate safety warning and technician escalation flag based on risk level."""
    if fault.risk_level == "red":
        return (
            "CRITICAL SAFETY WARNING: High electrical or thermal hazard. "
            "Immediately power down device and avoid charging. "
            "Certified technician escalation is required.",
            True,
        )
    elif fault.risk_level == "yellow":
        return (
            "HARDWARE ADVISORY: Internal component replacement recommended. "
            "Ensure device is disconnected from power before servicing.",
            True,
        )
    else:
        return (
            "MAINTENANCE INFO: Safe for user-level troubleshooting. "
            "Follow standard maintenance or settings instructions.",
            False,
        )


def generate_follow_up_question(
    device_slug: str,
    matches: list[dict],
    symptom: str,
) -> dict[str, Any] | None:
    """Generate a discriminating follow-up question for ambiguous hardware diagnoses."""
    if not matches:
        return None

    symptom_tokens = extract_tokens(symptom)
    fault_names = {m["fault"] for m in matches}

    for rule in FOLLOW_UP_RULES:
        if rule["device"] != device_slug:
            continue
        overlap_faults = rule["faults"] & fault_names
        overlap_keywords = rule["trigger_keywords"] & symptom_tokens
        if overlap_faults or overlap_keywords:
            return {
                "question": rule["question"],
                "options": rule["options"],
            }

    return None


def diagnose(
    db: Session,
    device_slug: str | None = None,
    symptom: str = "",
    language: str = "en",
    device: str | None = None,
) -> tuple[Device | None, list[dict]]:
    """
    Diagnose possible hardware faults for a device given a symptom description.

    Compares the symptom against seeded fault records using weighted keyword overlap,
    negation handling, synonym clustering, and safety tagging.
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
            safety_warning, req_tech = get_safety_details(fault)
            risk_map = {"red": "high", "yellow": "medium", "green": "low"}
            norm_risk = risk_map.get(fault.risk_level, "medium")
            candidates.append({
                "fault": fault.fault_name,
                "title": fault.fault_name,
                "match_score": score,
                "confidence": score,
                "confidence_score": score,
                "risk_level": fault.risk_level,
                "risk": norm_risk,
                "severity": norm_risk,
                "cost": f"KSh {fault.cost_min:,} - {fault.cost_max:,}",
                "cost_estimate": f"{fault.cost_min} - {fault.cost_max}",
                "currency": "KES",
                "estimated_cost": {
                    "min": fault.cost_min,
                    "max": fault.cost_max,
                    "currency": "KES",
                },
                "fix_steps": fault.fix_steps,
                "steps": fault.fix_steps,
                "description": fault.description or f"Hardware fault profile for {fault.fault_name}.",
                "safety_warning": safety_warning,
                "requires_technician": req_tech,
            })

    # Rank by match_score descending, then cost_min ascending
    candidates.sort(key=lambda item: (-item["match_score"], item["estimated_cost"]["min"]))

    return device_obj, candidates[:3]
