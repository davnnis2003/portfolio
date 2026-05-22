import pytest
from interpretation_layer.rule_engine import RuleEngine

@pytest.fixture
def engine():
    return RuleEngine()

def test_fassade_qualified(engine):
    intake = {
        "product": "fassade",
        "address": {"region": "NRW_SudNieder"},
        "fields": {
            "building_type": "EFH",
            "building_year": 1950,
            "mauerstarke_cm": 30,
            "fassaden_typ": "verputzt"
        }
    }
    status, reasons = engine.evaluate(intake)
    assert status == "QUALIFIED"
    assert not reasons

def test_fassade_universal_disqualification(engine):
    # Wall too thin
    intake = {
        "product": "fassade",
        "fields": {"mauerstarke_cm": 20}
    }
    status, reasons = engine.evaluate(intake)
    assert status == "DISQUALIFIED"
    assert "Mauerwerk 20 cm < 28 cm" in reasons[0]

    # Fachwerk
    intake = {
        "product": "fassade",
        "fields": {"building_type": "Fachwerkhaus"}
    }
    status, reasons = engine.evaluate(intake)
    assert status == "DISQUALIFIED"
    assert "Fachwerkhaus" in reasons[0]

def test_fassade_region_specific(engine):
    # Sud_Hessen_RLP is very strict
    intake = {
        "product": "fassade",
        "address": {"region": "Sud_Hessen_RLP"},
        "fields": {
            "building_year": 1960, # Rule says < 1950
            "mauerstarke_cm": 32,
            "fassaden_typ": "rotklinker"
        }
    }
    status, reasons = engine.evaluate(intake)
    assert status == "DISQUALIFIED"
    assert "Sud_Hessen_RLP" in reasons[0]

def test_ogd_disqualification(engine):
    intake = {
        "product": "ogd",
        "fields": {"dachboden_zukunft_wohnraum": True}
    }
    status, reasons = engine.evaluate(intake)
    assert status == "DISQUALIFIED"
    assert "Wohnraum" in reasons[0]

def test_kellerdecke_disqualification(engine):
    intake = {
        "product": "kellerdecke",
        "fields": {"feuchtigkeit": True}
    }
    status, reasons = engine.evaluate(intake)
    assert status == "DISQUALIFIED"
    assert "Feuchtigkeit" in reasons[0]
