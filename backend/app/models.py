from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone

class ActivityItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    time_slot: str = "morning"
    time_str: str = "09:00 AM - 11:30 AM"
    title: str
    category: str = "attraction"
    description: str
    location_name: str
    estimated_cost: float = 0.0
    booking_tip: Optional[str] = None
    transport_recommendation: Optional[str] = None
    tags: List[str] = []

class DayPlan(BaseModel):
    day_number: int
    date_str: Optional[str] = None
    theme: str
    summary: str
    activities: List[ActivityItem] = []
    accommodation_suggestion: Optional[str] = None
    day_budget_estimate: float = 0.0
    travel_logistics_note: Optional[str] = None

class CostBreakdown(BaseModel):
    currency: str = "USD"
    currency_symbol: str = "$"
    stay: float = 0.0
    dining: float = 0.0
    attractions: float = 0.0
    transport: float = 0.0
    misc: float = 0.0
    total: float = 0.0
    per_person: float = 0.0

class TripPreferences(BaseModel):
    destination: str
    start_date: str
    end_date: str
    traveler_type: Literal["solo", "couple", "group", "family"] = "solo"
    group_size: int = 1
    budget_tier: Literal["budget", "moderate", "luxury", "custom"] = "moderate"
    custom_budget: Optional[float] = None
    currency: str = "USD"
    interests: List[str] = ["sightseeing", "food"]
    pacing: Literal["relaxed", "moderate", "packed"] = "moderate"
    accommodation_pref: Literal["hostel", "budget_hotel", "boutique_hotel", "luxury_resort", "airbnb"] = "boutique_hotel"
    dietary_restrictions: Optional[str] = None
    special_requests: Optional[str] = None

class TripItinerary(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    destination: str
    start_date: str
    end_date: str
    duration_days: int
    traveler_type: str
    group_size: int = 1
    budget_tier: str
    currency: str = "USD"
    currency_symbol: str = "$"
    preferences: TripPreferences
    cost_breakdown: CostBreakdown
    days: List[DayPlan] = []
    packing_checklist: List[str] = []
    local_etiquette_tips: List[str] = []
    ai_rationale: str = ""
    generation_source: Literal["gemini", "local_fallback"] = "local_fallback"
    generation_model: str = "Adaptive Knowledge Engine"
    is_saved: bool = False
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RegenerateDayRequest(BaseModel):
    trip_id: str
    day_number: int
    custom_instructions: Optional[str] = "Make it more scenic and relaxed"

class RegenerateActivityRequest(BaseModel):
    trip_id: str
    day_number: int
    activity_id: str
    custom_instructions: Optional[str] = "Suggest a romantic dining alternative"

class UpdateTripRequest(BaseModel):
    title: Optional[str] = None
    days: Optional[List[DayPlan]] = None
    packing_checklist: Optional[List[str]] = None
    local_etiquette_tips: Optional[List[str]] = None
    notes: Optional[str] = None
    cost_breakdown: Optional[CostBreakdown] = None
