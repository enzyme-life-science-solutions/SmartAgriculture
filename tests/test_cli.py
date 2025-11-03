from smart_agriculture.cli import generate_insight


def test_generate_insight_uses_farm_name_when_present() -> None:
    config = {"insight": "Moisture stable.", "farm_name": "Field Alpha"}

    result = generate_insight(config)

    assert "Field Alpha" in result
    assert result.startswith("Moisture stable.")
