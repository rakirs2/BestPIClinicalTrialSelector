from pathlib import Path

from scrapers.clinicaltrials.transform import normalize_full_study


def test_normalize_full_study_loads_sample():
    sample_path = Path(__file__).with_name("sample_study.json")
    payload = sample_path.read_text(encoding="utf-8")

    import json

    data = json.loads(payload)
    normalized = normalize_full_study(data)

    assert normalized.study.nct_id == "NCT00000001"
    assert normalized.study.enrollment == 120
    assert normalized.conditions[0].name == "Condition A"
    assert normalized.interventions[0].name == "Drug A"
    assert normalized.locations[0].country == "United States"
