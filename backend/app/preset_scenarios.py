from typing import Dict, Any
from .models import TripPreferences

PRESET_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "scenario_1": {
        "id": "scenario_1",
        "title": "Solo Weekend Getaway to Tokyo",
        "badge": "Scenario 1: Solo Traveler",
        "tagline": "Quick 3-day high-efficiency urban exploration, budget-friendly ramen & iconic sights",
        "preferences": TripPreferences(
            destination="Tokyo, Japan",
            start_date="2026-11-06",
            end_date="2026-11-08",
            traveler_type="solo",
            group_size=1,
            budget_tier="budget",
            currency="USD",
            interests=["food", "sightseeing", "culture", "photography"],
            pacing="packed",
            accommodation_pref="hostel",
            dietary_restrictions="None (love local street food and ramen)",
            special_requests="Maximize time, avoid long queues, suggest solo-friendly dining and scenic photo spots near metro hubs."
        ).model_dump()
    },
    "scenario_2": {
        "id": "scenario_2",
        "title": "Romantic Couple Vacation in Amalfi Coast",
        "badge": "Scenario 2: Romantic Couple",
        "tagline": "5-day relaxed, scenic luxury escape with cliffside dining and sunset cruises",
        "preferences": TripPreferences(
            destination="Amalfi Coast, Italy",
            start_date="2026-12-10",
            end_date="2026-12-14",
            traveler_type="couple",
            group_size=2,
            budget_tier="luxury",
            currency="USD",
            interests=["romantic", "food", "relaxation", "nature", "photography"],
            pacing="relaxed",
            accommodation_pref="boutique_hotel",
            dietary_restrictions="Pescatarian friendly, fine Italian wine pairings",
            special_requests="Curate romantic sunset dinners, scenic coastal paths (Path of the Gods), private boat tour to Capri, and leisurely mornings."
        ).model_dump()
    },
    "scenario_3": {
        "id": "scenario_3",
        "title": "Friends Multi-Day Adventure in Banff & Canadian Rockies",
        "badge": "Scenario 3: Small Group Adventure",
        "tagline": "6-day coordinated trip balancing alpine hikes, group cabin stays, and wildlife tours",
        "preferences": TripPreferences(
            destination="Banff National Park, Canada",
            start_date="2026-11-15",
            end_date="2026-11-20",
            traveler_type="group",
            group_size=5,
            budget_tier="moderate",
            currency="USD",
            interests=["adventure", "nature", "sightseeing", "food"],
            pacing="moderate",
            accommodation_pref="airbnb",
            dietary_restrictions="1 Vegetarian in the group",
            special_requests="Plan activities suitable for 5 people, minimize vehicle parking stress, include group lodge dining, and buffer time between hikes."
        ).model_dump()
    }
}
