import pytest
from app.core.database import SessionLocal
from app.models.device import Device
from app.models.fault import Fault
from app.services.diagnostic_engine import (
    normalize_text,
    extract_tokens,
    strip_swahili_prefixes,
    has_negation,
    split_into_clauses,
    calculate_match_score,
    get_safety_details,
    generate_follow_up_question,
    diagnose,
    MINIMUM_MATCH_SCORE,
    MAXIMUM_MATCH_SCORE,
    SYNONYM_MAP,
)


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------
# 1. Normalization & Tokenization Tests
# ---------------------------------------------------------

def test_normalize_text_english():
    text = "My Phone's Battery Drains VERY Quickly!!!"
    norm = normalize_text(text)
    assert norm == "my phone s battery drains very quickly"


def test_normalize_text_swahili():
    text = "SIMU YANGU INAZIMA HARAKA, betri hai-shiki chaji!"
    norm = normalize_text(text)
    assert "simu yangu inazima haraka" in norm
    assert "betri" in norm


def test_extract_tokens_stop_words_english():
    tokens = extract_tokens("My phone battery drains very quickly", language="en")
    assert "battery" in tokens
    assert "drains" in tokens
    assert "quickly" in tokens
    assert "my" not in tokens
    assert "phone" not in tokens
    assert "very" not in tokens


def test_extract_tokens_stop_words_swahili():
    tokens = extract_tokens("Simu yangu inazima lakini screen ni nyeusi", language="sw")
    assert "screen" in tokens
    assert "nyeusi" in tokens
    assert "inazima" in tokens
    assert "simu" not in tokens
    assert "yangu" not in tokens
    assert "lakini" not in tokens
    assert "ni" not in tokens


def test_swahili_prefix_stripping():
    assert strip_swahili_prefixes("imecrack") == "crack"
    assert strip_swahili_prefixes("inachemka") == "chemka"
    assert strip_swahili_prefixes("kuconnect") == "connect"
    assert strip_swahili_prefixes("imepasuka") == "pasuka"


# ---------------------------------------------------------
# 2. Synonym & Code-Switching Tests
# ---------------------------------------------------------

def test_synonym_canonicalization_screen():
    for word in ("kioo", "skrini", "display", "monitor", "panel"):
        tokens = extract_tokens(f"the {word} is faulty")
        assert "screen" in tokens


def test_synonym_canonicalization_battery():
    for word in ("betri", "power", "chaji", "charge"):
        tokens = extract_tokens(f"the {word} problem")
        assert "battery" in tokens


def test_synonym_canonicalization_broken():
    for word in ("cracked", "imepasuka", "imevunjika", "imecrack", "shattered"):
        tokens = extract_tokens(f"device {word}")
        assert "broken" in tokens


def test_code_switching_sheng_imecrack():
    tokens = extract_tokens("Screen imecrack vibaya")
    assert "screen" in tokens
    assert "broken" in tokens or "crack" in tokens


def test_code_switching_sheng_ha_charge():
    tokens = extract_tokens("Simu yangu ha-charge kabisa")
    assert "battery" in tokens or "charge" in tokens


# ---------------------------------------------------------
# 3. Negation Detection Tests
# ---------------------------------------------------------

def test_has_negation_english():
    assert has_negation("battery does not drain quickly") is True
    assert has_negation("screen is not broken") is True
    assert has_negation("phone cannot connect to wifi") is True
    assert has_negation("battery drains quickly") is False


def test_has_negation_swahili():
    assert has_negation("betri haizimi") is True
    assert has_negation("screen haijavunjika") is True
    assert has_negation("simu haiwaki") is True
    assert has_negation("screen ni nyeusi") is False


def test_clause_splitting_with_contrast():
    clauses = split_into_clauses("Battery does not drain quickly, but screen is cracked")
    assert len(clauses) == 2
    clause1, neg1 = clauses[0]
    clause2, neg2 = clauses[1]
    assert "battery" in clause1.lower()
    assert neg1 is True
    assert "screen" in clause2.lower()
    assert neg2 is False


def test_negation_contradiction_filters_fault(db):
    score = calculate_match_score(
        symptom="Battery does not drain quickly and battery health is not poor",
        keywords=["battery drains quickly", "battery health is poor"],
        language="en",
    )
    assert score == 0


def test_negated_clause_leaves_affirmative_fault_intact(db):
    _, matches = diagnose(
        db=db,
        device_slug="phone",
        symptom="Battery does not drain quickly, but screen is cracked and shattered",
        language="en",
    )
    assert len(matches) > 0
    top_fault = matches[0]["fault"]
    assert top_fault == "Broken display panel"
    fault_names = [m["fault"] for m in matches]
    assert "Battery degradation" not in fault_names


def test_swahili_negation_handling(db):
    _, matches = diagnose(
        db=db,
        device_slug="phone",
        symptom="Betri haizimi, lakini screen imevunjika",
        language="sw",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "Broken display panel"


# ---------------------------------------------------------
# 4. English Diagnostic Accuracy Tests (Phone, Laptop, Router)
# ---------------------------------------------------------

def test_phone_battery_degradation(db):
    _, matches = diagnose(
        db=db,
        device_slug="phone",
        symptom="My phone battery drains very quickly",
        language="en",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "Battery degradation"
    assert matches[0]["match_score"] == 95


def test_phone_charging_port_damage(db):
    _, matches = diagnose(
        db=db,
        device_slug="phone",
        symptom="Charging cable feels loose and phone only charges at an angle",
        language="en",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "Charging port damage"


def test_phone_broken_display_panel(db):
    _, matches = diagnose(
        db=db,
        device_slug="phone",
        symptom="Cracked glass screen with display lines",
        language="en",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "Broken display panel"


def test_phone_water_damage_red_risk(db):
    _, matches = diagnose(
        db=db,
        device_slug="phone",
        symptom="Phone dropped in water liquid ingress moisture detected",
        language="en",
    )
    assert len(matches) > 0
    top = matches[0]
    assert top["fault"] == "Water or liquid ingress"
    assert top["risk_level"] == "red"
    assert top["requires_technician"] is True
    assert "CRITICAL" in top["safety_warning"]


def test_laptop_ram_fault_black_screen(db):
    _, matches = diagnose(
        db=db,
        device_slug="laptop",
        symptom="Laptop powers on and fans spin but display is completely black",
        language="en",
    )
    assert len(matches) > 0
    fault_names = [m["fault"] for m in matches]
    assert any(f in fault_names for f in ("RAM fault", "Display panel failure"))


def test_laptop_ssd_failure(db):
    _, matches = diagnose(
        db=db,
        device_slug="laptop",
        symptom="Laptop says no boot device disk error",
        language="en",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "SSD or hard drive failure"


def test_laptop_cooling_fan_overheating(db):
    _, matches = diagnose(
        db=db,
        device_slug="laptop",
        symptom="Laptop is overheating fan making loud grinding noise and shutting down",
        language="en",
    )
    assert len(matches) > 0
    fault_names = [m["fault"] for m in matches]
    assert any(f in fault_names for f in ("Cooling fan failure", "Dust-clogged cooling system"))


def test_laptop_keyboard_failure(db):
    _, matches = diagnose(
        db=db,
        device_slug="laptop",
        symptom="Keyboard types wrong characters and keys are stuck",
        language="en",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "Keyboard failure"


def test_router_wan_cable_fault(db):
    _, matches = diagnose(
        db=db,
        device_slug="router",
        symptom="Router WAN port light is red and ethernet cable unplugged",
        language="en",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "WAN cable or port fault"


def test_router_dns_failure(db):
    _, matches = diagnose(
        db=db,
        device_slug="router",
        symptom="Connected to Wi-Fi but websites do not load DNS probe finished nxdomain",
        language="en",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "DNS resolution failure"


def test_router_weak_wifi_coverage(db):
    _, matches = diagnose(
        db=db,
        device_slug="router",
        symptom="Wi-Fi weak in another room and connection drops far from router",
        language="en",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "Weak Wi-Fi signal or coverage"


# ---------------------------------------------------------
# 5. Kiswahili & Mixed-Language Diagnostic Tests
# ---------------------------------------------------------

def test_swahili_phone_battery(db):
    _, matches = diagnose(
        db=db,
        device_slug="phone",
        symptom="Simu yangu inazima haraka na betri inaisha",
        language="sw",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "Battery degradation"


def test_swahili_laptop_ram_black_screen(db):
    _, matches = diagnose(
        db=db,
        device_slug="laptop",
        symptom="Laptop yangu inawaka lakini screen ni nyeusi",
        language="sw",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "RAM fault"
    assert matches[0]["match_score"] == 95


def test_swahili_phone_water_ingress(db):
    _, matches = diagnose(
        db=db,
        device_slug="phone",
        symptom="Simu imelowa kwenye maji haitaki kuwaka",
        language="sw",
    )
    assert len(matches) > 0
    assert matches[0]["fault"] == "Water or liquid ingress"
    assert matches[0]["risk_level"] == "red"


def test_swahili_router_outage(db):
    _, matches = diagnose(
        db=db,
        device_slug="router",
        symptom="Hakuna mtandao taa ya internet inawaka nyekundu",
        language="sw",
    )
    assert len(matches) > 0
    fault_names = [m["fault"] for m in matches]
    assert any("outage" in f.lower() or "wan" in f.lower() for f in fault_names)


# ---------------------------------------------------------
# 6. Safety, Escalation, Capping & Threshold Tests
# ---------------------------------------------------------

def test_weak_evidence_rejection(db):
    _, matches = diagnose(
        db=db,
        device_slug="phone",
        symptom="The weather in Nairobi is sunny and warm",
        language="en",
    )
    assert matches == []


def test_generic_symptom_rejection(db):
    _, matches = diagnose(
        db=db,
        device_slug="laptop",
        symptom="Something is wrong",
        language="en",
    )
    assert matches == []


def test_score_capping_at_95(db):
    _, matches = diagnose(
        db=db,
        device_slug="phone",
        symptom="battery drains quickly",
        language="en",
    )
    assert len(matches) > 0
    for match in matches:
        assert match["match_score"] <= MAXIMUM_MATCH_SCORE


def test_score_threshold_minimum_20(db):
    _, matches = diagnose(
        db=db,
        device_slug="laptop",
        symptom="blue screen operating system error",
        language="en",
    )
    assert len(matches) > 0
    for match in matches:
        assert match["match_score"] >= MINIMUM_MATCH_SCORE


def test_safety_details_for_risk_levels():
    red_fault = Fault(risk_level="red")
    yellow_fault = Fault(risk_level="yellow")
    green_fault = Fault(risk_level="green")

    red_warn, red_tech = get_safety_details(red_fault)
    assert "CRITICAL" in red_warn
    assert red_tech is True

    yellow_warn, yellow_tech = get_safety_details(yellow_fault)
    assert "ADVISORY" in yellow_warn
    assert yellow_tech is True

    green_warn, green_tech = get_safety_details(green_fault)
    assert "MAINTENANCE" in green_warn
    assert green_tech is False


# ---------------------------------------------------------
# 7. Follow-Up Question Generation Tests
# ---------------------------------------------------------

def test_follow_up_question_black_screen(db):
    device, matches = diagnose(
        db=db,
        device_slug="laptop",
        symptom="Laptop screen is black",
        language="en",
    )
    q = generate_follow_up_question("laptop", matches, "Laptop screen is black")
    assert q is not None
    assert "external monitor" in q["question"].lower()
    assert len(q["options"]) >= 2


def test_follow_up_question_charging_port(db):
    device, matches = diagnose(
        db=db,
        device_slug="phone",
        symptom="Phone does not charge",
        language="en",
    )
    q = generate_follow_up_question("phone", matches, "Phone does not charge")
    assert q is not None
    assert "charger" in q["question"].lower() or "cable" in q["question"].lower()


def test_ranking_consistency(db):
    _, matches = diagnose(
        db=db,
        device_slug="laptop",
        symptom="Laptop inawaka lakini screen ni nyeusi",
        language="sw",
    )
    assert len(matches) >= 2
    # Ensure ranked in descending order of match_score
    scores = [m["match_score"] for m in matches]
    assert scores == sorted(scores, reverse=True)


def test_unknown_device_returns_none(db):
    device, matches = diagnose(
        db=db,
        device_slug="smartwatch",
        symptom="Screen is cracked",
        language="en",
    )
    assert device is None
    assert matches == []
