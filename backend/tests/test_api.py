import pytest
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.main import (
    get_health, get_preset_scenarios, generate_quick_scenario,
    generate_trip, save_trip, get_trip, update_trip, regenerate_day,
    export_markdown, delete_trip
)
from backend.app.models import TripPreferences, RegenerateDayRequest, UpdateTripRequest

def test_health():
    health = get_health()
    assert health["status"] == "healthy"
    assert "ai_engine" in health
    assert "storage" in health
    assert "supported_currencies" in health

def test_presets():
    presets = get_preset_scenarios()
    assert len(presets) >= 3

def test_multi_currency_inr():
    prefs = TripPreferences(
        destination="Mumbai, India",
        start_date="2026-11-01",
        end_date="2026-11-04",
        traveler_type="solo",
        group_size=1,
        budget_tier="moderate",
        currency="INR"
    )
    trip = generate_trip(prefs)
    assert trip.currency == "INR"
    assert trip.currency_symbol == "₹"
    assert trip.duration_days == 4
    assert len(trip.days) == 4
    assert trip.cost_breakdown.total > 0

def test_non_repeating_activities():
    prefs = TripPreferences(
        destination="London, UK",
        start_date="2026-12-01",
        end_date="2026-12-06",
        traveler_type="couple",
        group_size=2,
        budget_tier="luxury",
        currency="GBP"
    )
    trip = generate_trip(prefs)
    assert trip.duration_days == 6
    assert len(trip.days) == 6
    titles = [a.title for d in trip.days for a in d.activities]
    assert len(titles) == len(set(titles)), "Duplicate activity titles found!"

def test_crud_and_edit():
    s1 = generate_quick_scenario("scenario_1")
    trip_id = s1.id
    
    # Save
    save_trip(s1)
    
    # Get
    fetched = get_trip(trip_id)
    assert fetched.id == trip_id
    
    # Update
    updated = update_trip(trip_id, UpdateTripRequest(title="Updated Solo Adventure"))
    assert updated.title == "Updated Solo Adventure"
    
    # Delete
    delete_trip(trip_id)
