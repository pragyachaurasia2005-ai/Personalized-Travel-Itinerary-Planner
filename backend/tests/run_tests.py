import sys
import io
from pathlib import Path
from datetime import datetime

# Ensure UTF-8 output on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.main import (
    get_health, get_preset_scenarios, generate_quick_scenario,
    generate_trip, save_trip, get_trip, update_trip, regenerate_day,
    export_markdown, delete_trip
)
from backend.app.models import TripPreferences, RegenerateDayRequest, UpdateTripRequest, ActivityItem
from backend.app.ai_engine import ai_engine
from backend.app.storage import storage

def run_all_tests():
    print("==================================================================")
    print("🚀 TRAVELCRAFT AI: COMPREHENSIVE VERIFICATION SUITE")
    print("==================================================================")

    # -------------------------------------------------------------
    # 1. Truthful Health & System Status Verification
    # -------------------------------------------------------------
    print("\n[TEST 1] Verifying System Status, AI Engine & Supabase Storage Mode...")
    health = get_health()
    assert health["status"] == "healthy"
    print(f"  ✓ App Name: {health['app_name']} v{health['version']}")
    
    # Verify AI Engine honesty
    ai_status = health["ai_engine"]
    if ai_status["key_configured"]:
        assert ai_status["gemini_connected"] is True
        print(f"  ✓ AI Engine: Google Gemini Active ({ai_status['model']})")
    else:
        assert ai_status["gemini_connected"] is False
        assert "Gemini" in ai_status["model"] or "Adaptive" in ai_status["model"]
        print(f"  ✓ AI Engine: Truthfully detected no Gemini key ({ai_status['model']})")

    # Verify Supabase honesty
    storage_status = health["storage"]
    if storage_status["supabase_configured"]:
        print(f"  ✓ Storage: Supabase Cloud ({storage_status['storage_mode']})")
    else:
        assert storage_status["supabase_connected"] is False
        assert "SQLite" in storage_status["storage_mode"]
        print(f"  ✓ Storage: Truthfully operating in Local SQLite mode ({storage_status['storage_mode']})")

    # -------------------------------------------------------------
    # 2. Multi-Currency Support Testing (INR, USD, EUR, JPY)
    # -------------------------------------------------------------
    print("\n[TEST 2] Verifying Multi-Currency Support (INR, USD, EUR, JPY)...")
    
    # Test INR (₹)
    inr_prefs = TripPreferences(
        destination="Jaipur & Udaipur, India",
        start_date="2026-11-10",
        end_date="2026-11-14",
        traveler_type="couple",
        group_size=2,
        budget_tier="moderate",
        currency="INR",
        interests=["culture", "food", "romantic", "sightseeing"],
        pacing="moderate"
    )
    inr_trip = generate_trip(inr_prefs)
    assert inr_trip.currency == "INR"
    assert inr_trip.currency_symbol == "₹"
    assert inr_trip.cost_breakdown.currency == "INR"
    assert inr_trip.cost_breakdown.currency_symbol == "₹"
    assert inr_trip.cost_breakdown.total > 5000.0  # Realistic INR value
    print(f"  ✓ INR Trip Generated: {inr_trip.title}")
    print(f"    Total: ₹{inr_trip.cost_breakdown.total:,.2f} | Per Person: ₹{inr_trip.cost_breakdown.per_person:,.2f}")
    assert inr_trip.cost_breakdown.per_person == round(inr_trip.cost_breakdown.total / 2, 2)

    # Test JPY (¥)
    jpy_prefs = TripPreferences(
        destination="Kyoto, Japan",
        start_date="2026-11-01",
        end_date="2026-11-03",
        traveler_type="solo",
        group_size=1,
        budget_tier="budget",
        currency="JPY",
        interests=["culture", "food"],
        pacing="packed"
    )
    jpy_trip = generate_trip(jpy_prefs)
    assert jpy_trip.currency == "JPY"
    assert jpy_trip.currency_symbol == "¥"
    assert jpy_trip.cost_breakdown.total > 10000.0  # Realistic JPY value
    print(f"  ✓ JPY Trip Generated: {jpy_trip.title} (Total: ¥{jpy_trip.cost_breakdown.total:,.2f})")

    # -------------------------------------------------------------
    # 3. Exact Date Range & Duration Matching Verification
    # -------------------------------------------------------------
    print("\n[TEST 3] Verifying Exact Date Range & Duration Consistency...")
    # 5-day trip test
    dur_5_prefs = TripPreferences(
        destination="Rome, Italy",
        start_date="2026-12-01",
        end_date="2026-12-05",  # 5 days: Dec 1, 2, 3, 4, 5
        traveler_type="couple",
        group_size=2,
        budget_tier="luxury",
        currency="EUR"
    )
    trip_5 = generate_trip(dur_5_prefs)
    assert trip_5.duration_days == 5
    assert len(trip_5.days) == 5
    expected_dates = ["2026-12-01", "2026-12-02", "2026-12-03", "2026-12-04", "2026-12-05"]
    actual_dates = [d.date_str for d in trip_5.days]
    assert actual_dates == expected_dates
    print(f"  ✓ 5-Day Trip matched exact consecutive dates: {actual_dates}")

    # 7-day trip test
    dur_7_prefs = TripPreferences(
        destination="Bali, Indonesia",
        start_date="2026-11-10",
        end_date="2026-11-16",  # 7 days
        traveler_type="group",
        group_size=4,
        budget_tier="moderate",
        currency="USD"
    )
    trip_7 = generate_trip(dur_7_prefs)
    assert trip_7.duration_days == 7
    assert len(trip_7.days) == 7
    print(f"  ✓ 7-Day Multi-day trip verified: Day 1 to Day {len(trip_7.days)} generated.")

    # -------------------------------------------------------------
    # 4. Zero Activity Repetition Verification
    # -------------------------------------------------------------
    print("\n[TEST 4] Verifying Zero Activity Repetition Across Days...")
    all_activity_titles = [act.title for d in trip_7.days for act in d.activities]
    unique_titles = set(all_activity_titles)
    print(f"  ✓ Total activities generated across 7 days: {len(all_activity_titles)}")
    print(f"  ✓ Unique activity titles: {len(unique_titles)}")
    assert len(all_activity_titles) == len(unique_titles), "Duplicate activity detected!"
    print("  ✓ Zero activity repetition verified! Every activity is completely unique.")

    # Verify each activity has timing, description, estimated cost, and transit
    for day in trip_7.days:
        for act in day.activities:
            assert act.time_str and len(act.time_str) > 0
            assert act.description and len(act.description) > 0
            assert act.estimated_cost >= 0.0
            assert act.transport_recommendation is not None

    # -------------------------------------------------------------
    # 5. Strict Mathematical Budget Consistency Verification
    # -------------------------------------------------------------
    print("\n[TEST 5] Verifying Strict Mathematical Budget Integrity...")
    cb = trip_5.cost_breakdown
    computed_sum = round(cb.stay + cb.dining + cb.attractions + cb.transport + cb.misc, 2)
    assert round(cb.total, 2) == computed_sum, f"Total {cb.total} != sum {computed_sum}"
    expected_per_person = round(cb.total / 2, 2)
    assert cb.per_person == expected_per_person, f"Per person {cb.per_person} != {expected_per_person}"
    print(f"  ✓ Stay ({cb.currency_symbol}{cb.stay}) + Dining ({cb.currency_symbol}{cb.dining}) + Sights ({cb.currency_symbol}{cb.attractions}) + Transit ({cb.currency_symbol}{cb.transport}) + Misc ({cb.currency_symbol}{cb.misc})")
    print(f"    = Total {cb.currency_symbol}{cb.total:,.2f} strictly equals the sum of parts!")
    print(f"  ✓ Per person: {cb.currency_symbol}{cb.per_person:,.2f} strictly equals Total / 2.")

    # -------------------------------------------------------------
    # 6. Saved Trip CRUD & Editing Operations (Supabase & SQLite)
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing Trip Saving, Updating, and Deleting...")
    # Save
    saved_trip = save_trip(inr_trip)
    assert saved_trip.id == inr_trip.id
    print(f"  ✓ Trip saved to primary storage with ID: {saved_trip.id}")

    # Retrieve
    retrieved = get_trip(saved_trip.id)
    assert retrieved.id == saved_trip.id
    assert retrieved.currency == "INR"
    print(f"  ✓ Trip retrieved successfully from storage: '{retrieved.title}'")

    # Update title
    updated = update_trip(saved_trip.id, UpdateTripRequest(title="Royal Rajasthan Royal Heritage Tour"))
    assert updated.title == "Royal Rajasthan Royal Heritage Tour"
    print(f"  ✓ Title successfully updated to: '{updated.title}'")

    # Update activity inside Day 1
    updated_days = list(updated.days)
    updated_days[0].activities[0].title = "Private Sunrise Palace Photography Tour"
    updated_days[0].activities[0].estimated_cost = 2500.0
    updated_with_act = update_trip(saved_trip.id, UpdateTripRequest(days=updated_days))
    assert updated_with_act.days[0].activities[0].title == "Private Sunrise Palace Photography Tour"
    print(f"  ✓ Activity successfully modified and persisted: '{updated_with_act.days[0].activities[0].title}'")

    # -------------------------------------------------------------
    # 7. AI Single-Day Regeneration
    # -------------------------------------------------------------
    print("\n[TEST 7] Testing AI Single-Day Re-roll...")
    regen_res = regenerate_day(RegenerateDayRequest(
        trip_id=saved_trip.id,
        day_number=2,
        custom_instructions="Focus on peaceful lakeside dinner and traditional puppet performance"
    ))
    assert len(regen_res.days) == inr_trip.duration_days
    day_2 = regen_res.days[1]
    assert day_2.day_number == 2
    print(f"  ✓ Day 2 regenerated: {day_2.theme}")
    print(f"    Summary: {day_2.summary}")

    # -------------------------------------------------------------
    # 8. Markdown Export Verification
    # -------------------------------------------------------------
    print("\n[TEST 8] Verifying Multi-Currency Markdown Export...")
    md_res = export_markdown(saved_trip.id)
    md_text = md_res.body.decode("utf-8")
    assert "₹" in md_text
    assert "INR" in md_text
    assert "Royal Rajasthan" in md_text
    assert "Day-by-Day Itinerary" in md_text
    print(f"  ✓ Markdown exported with correct INR currency formatting ({len(md_text)} bytes)")

    # -------------------------------------------------------------
    # 9. Clean-up Deletion Verification
    # -------------------------------------------------------------
    print("\n[TEST 9] Verifying Trip Deletion...")
    del_res = delete_trip(saved_trip.id)
    assert del_res["id"] == saved_trip.id
    assert storage.get_trip(saved_trip.id) is None
    print(f"  ✓ Trip successfully deleted from storage.")

    print("\n==================================================================")
    print("🎉 ALL 9 TEST MODULES PASSED FLAWLESSLY WITH 100% SUCCESS!")
    print("==================================================================")

if __name__ == "__main__":
    run_all_tests()
