import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse

from .config import settings, BASE_DIR, reload_environment
from .models import (
    TripPreferences, TripItinerary, RegenerateDayRequest, 
    UpdateTripRequest
)
from .ai_engine import ai_engine
from .storage import storage
from .preset_scenarios import PRESET_SCENARIOS
from .export_utils import trip_to_markdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Full-stack AI-Powered Personalized Travel Itinerary Planner"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = BASE_DIR / "frontend"

@app.get("/api/health")
def get_health():
    """Returns application health, dynamic AI engine status, and truthful Supabase storage mode."""
    reload_environment()
    storage_status = storage.get_status()
    ai_status = ai_engine.get_status()

    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "ai_engine": ai_status,
        "storage": storage_status,
        "supported_currencies": settings.CURRENCY_CONFIG
    }

@app.get("/api/presets")
def get_preset_scenarios():
    """Returns the 3 key built-in scenarios."""
    return list(PRESET_SCENARIOS.values())

@app.post("/api/trips/quick-scenario/{scenario_key}")
def generate_quick_scenario(scenario_key: str, currency: str = "USD"):
    """Instantly generates one of the three core scenarios with chosen currency."""
    if scenario_key not in PRESET_SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario key not found")
    preset_data = PRESET_SCENARIOS[scenario_key]
    prefs_dict = dict(preset_data["preferences"])
    prefs_dict["currency"] = str(currency)
    prefs = TripPreferences(**prefs_dict)
    
    itinerary = ai_engine.generate_itinerary(prefs)
    itinerary.is_saved = True
    storage.save_trip(itinerary.model_dump())
    return itinerary

@app.post("/api/trips/generate", response_model=TripItinerary)
def generate_trip(prefs: TripPreferences):
    """Generates a complete day-by-day itinerary tailored to user preferences."""
    try:
        itinerary = ai_engine.generate_itinerary(prefs)
        return itinerary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/api/trips", response_model=TripItinerary)
def save_trip(trip: TripItinerary):
    """Saves or updates a trip in storage (Supabase primary when available, else SQLite)."""
    trip.is_saved = True
    saved_data = storage.save_trip(trip.model_dump())
    return TripItinerary(**saved_data)

@app.get("/api/trips")
def list_trips(search: str = Query(None), traveler_type: str = Query(None)):
    """Lists saved trips with optional search and traveler_type filter."""
    return storage.list_trips(search=search, traveler_type=traveler_type)

@app.get("/api/trips/{trip_id}", response_model=TripItinerary)
def get_trip(trip_id: str):
    """Fetches a saved trip by ID."""
    trip = storage.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return TripItinerary(**trip)

@app.put("/api/trips/{trip_id}", response_model=TripItinerary)
def update_trip(trip_id: str, update_req: UpdateTripRequest):
    """Updates mutable properties of an itinerary (title, activities, checklist, notes)."""
    existing = storage.get_trip(trip_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip_obj = TripItinerary(**existing)
    if update_req.title is not None:
        trip_obj.title = update_req.title
    if update_req.days is not None:
        trip_obj.days = update_req.days
        # Recalculate total estimated cost to preserve mathematical consistency
        new_attract = sum(sum(a.estimated_cost for a in d.activities if a.category in ["attraction", "experience", "relaxation"]) for d in trip_obj.days)
        trip_obj.cost_breakdown.attractions = round(new_attract, 2)
        trip_obj.cost_breakdown.total = round(
            trip_obj.cost_breakdown.stay + 
            trip_obj.cost_breakdown.dining + 
            trip_obj.cost_breakdown.attractions + 
            trip_obj.cost_breakdown.transport + 
            trip_obj.cost_breakdown.misc, 
            2
        )
        trip_obj.cost_breakdown.per_person = round(trip_obj.cost_breakdown.total / max(1, trip_obj.group_size), 2)
        
    if update_req.packing_checklist is not None:
        trip_obj.packing_checklist = update_req.packing_checklist
    if update_req.local_etiquette_tips is not None:
        trip_obj.local_etiquette_tips = update_req.local_etiquette_tips
    if update_req.notes is not None:
        trip_obj.notes = update_req.notes
    if update_req.cost_breakdown is not None:
        trip_obj.cost_breakdown = update_req.cost_breakdown

    saved = storage.update_trip(trip_id, trip_obj.model_dump())
    return TripItinerary(**saved)

@app.delete("/api/trips/{trip_id}")
def delete_trip(trip_id: str):
    """Deletes a trip from storage (Supabase & SQLite)."""
    success = storage.delete_trip(trip_id)
    if not success:
        raise HTTPException(status_code=404, detail="Trip could not be deleted")
    return {"message": "Trip successfully deleted", "id": trip_id}

@app.post("/api/trips/regenerate-day", response_model=TripItinerary)
def regenerate_day(req: RegenerateDayRequest):
    """Regenerates a single specific day in the itinerary."""
    existing = storage.get_trip(req.trip_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip_obj = TripItinerary(**existing)
    updated_trip = ai_engine.regenerate_day(
        trip=trip_obj,
        day_number=req.day_number,
        custom_instructions=req.custom_instructions or "Refine activities"
    )
    storage.save_trip(updated_trip.model_dump())
    return updated_trip

@app.get("/api/trips/{trip_id}/export/markdown")
def export_markdown(trip_id: str):
    """Exports the trip as formatted Markdown."""
    existing = storage.get_trip(trip_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip_obj = TripItinerary(**existing)
    md_content = trip_to_markdown(trip_obj)
    safe_dest = trip_obj.destination.replace(" ", "_").replace(",", "")
    return PlainTextResponse(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="trip_{safe_dest}.md"'}
    )

# Static frontend mount
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_frontend_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Frontend index.html is being prepared."}
