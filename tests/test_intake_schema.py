"""
Basic tests for intake schema validation
"""

import json
from datetime import datetime, date
from schemas.intake_schema import IntakeData, EXAMPLE_INTAKE


def test_intake_data_creation():
    """Test creating IntakeData with valid data"""
    data = IntakeData(
        week_start=date(2024, 1, 15),
        days_needed=5,
        away_days=[5, 6],
        avoid_ingredients=["エビ", "カニ"],
        max_cooking_time=30
    )
    
    assert data.week_start == date(2024, 1, 15)
    assert data.days_needed == 5
    assert data.away_days == [5, 6]
    assert data.avoid_ingredients == ["エビ", "カニ"]
    assert data.max_cooking_time == 30


def test_intake_data_defaults():
    """Test default values are applied correctly"""
    data = IntakeData(week_start=date(2024, 1, 15))
    
    assert data.days_needed == 7
    assert data.away_days == []
    assert data.avoid_ingredients == []
    assert data.max_cooking_time == 60
    assert data.guests_expected == 0


def test_intake_data_validation():
    """Test validation constraints"""
    # Test days_needed range
    try:
        IntakeData(week_start=date(2024, 1, 15), days_needed=0)
        assert False, "Should raise ValueError for days_needed=0"
    except ValueError:
        pass
    
    try:
        IntakeData(week_start=date(2024, 1, 15), days_needed=8)
        assert False, "Should raise ValueError for days_needed=8"
    except ValueError:
        pass
    
    # Test max_cooking_time range
    try:
        IntakeData(week_start=date(2024, 1, 15), max_cooking_time=5)
        assert False, "Should raise ValueError for max_cooking_time=5"
    except ValueError:
        pass
    
    try:
        IntakeData(week_start=date(2024, 1, 15), max_cooking_time=200)
        assert False, "Should raise ValueError for max_cooking_time=200"
    except ValueError:
        pass


def test_example_intake_parsing():
    """Test that example intake can be parsed"""
    # Convert date strings to date objects for validation
    example_data = EXAMPLE_INTAKE.copy()
    example_data['week_start'] = date.fromisoformat(example_data['week_start'])
    example_data['timestamp'] = datetime.fromisoformat(example_data['timestamp'])
    
    data = IntakeData(**example_data)
    
    assert isinstance(data, IntakeData)
    assert data.week_start == date(2024, 1, 15)
    assert data.days_needed == 5
    assert data.away_days == [5, 6]


def test_json_serialization():
    """Test JSON serialization works correctly"""
    data = IntakeData(
        week_start=date(2024, 1, 15),
        days_needed=5,
        avoid_ingredients=["エビ"]
    )
    
    # Test that we can serialize to JSON
    json_str = data.model_dump_json()
    parsed = json.loads(json_str)
    
    assert parsed['week_start'] == '2024-01-15'
    assert parsed['days_needed'] == 5
    assert parsed['avoid_ingredients'] == ["エビ"]


if __name__ == "__main__":
    # Run basic tests
    test_intake_data_creation()
    test_intake_data_defaults()
    test_intake_data_validation()
    test_example_intake_parsing()
    test_json_serialization()
    
    print("All tests passed!")