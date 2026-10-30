import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Set
from .config import settings, reload_environment
from .models import TripPreferences, TripItinerary, DayPlan, ActivityItem, CostBreakdown

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self):
        self.last_error = None
        self._init_gemini()

    def _init_gemini(self):
        reload_environment()
        self.api_key = settings.GEMINI_API_KEY.strip().strip('"').strip("'")
        self.model_name = settings.GEMINI_MODEL.strip() or "gemini-2.5-flash"
        self.client = None
        self.last_error = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Google Gemini client initialized with model: {self.model_name}")
            except Exception as e:
                self.last_error = f"Failed to initialize GenAI client: {str(e)}"
                logger.warning(self.last_error)
                self.client = None

    def is_ai_live(self) -> bool:
        """Returns True if Gemini API key is configured and client initialized."""
        reload_environment()
        new_key = settings.GEMINI_API_KEY.strip().strip('"').strip("'")
        if new_key and new_key != self.api_key:
            self._init_gemini()
        return bool(self.api_key and self.client)

    def get_status(self) -> Dict[str, Any]:
        live = self.is_ai_live()
        return {
            "gemini_connected": live,
            "model": self.model_name if live else "Adaptive Local Engine (Gemini Key Not Configured)",
            "provider": "Google Gemini" if live else "Local Heuristic Engine",
            "key_configured": bool(self.api_key),
            "last_error": self.last_error
        }

    def generate_itinerary(self, prefs: TripPreferences) -> TripItinerary:
        """Generates itinerary using live Gemini API if available, else adaptive local fallback."""
        start_dt = datetime.strptime(prefs.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(prefs.end_date, "%Y-%m-%d")
        duration = max(1, (end_dt - start_dt).days + 1)

        curr_info = settings.CURRENCY_CONFIG.get(prefs.currency, settings.CURRENCY_CONFIG["USD"])
        currency_code = prefs.currency
        currency_sym = curr_info["symbol"]
        conv_rate = curr_info["rate"]

        # Attempt Gemini Generation if configured
        if self.is_ai_live():
            try:
                logger.info(f"Generating itinerary via Google Gemini API ({self.model_name})...")
                ai_result = self._generate_with_gemini(prefs, duration, currency_code, currency_sym)
                if ai_result:
                    self.last_error = None
                    return ai_result
            except Exception as e:
                self._handle_gemini_error(e)
                logger.error(f"Gemini API generation error: {self.last_error}. Falling back to local adaptive engine.")

        # Local Adaptive Engine Fallback
        logger.info(f"Generating itinerary via Adaptive Local Engine for {prefs.destination} ({duration} days)...")
        return self._generate_adaptive_itinerary(prefs, duration, currency_code, currency_sym, conv_rate)

    def _handle_gemini_error(self, e: Exception):
        """Categorizes Gemini API errors for clear reporting."""
        err_str = str(e)
        if "API_KEY_INVALID" in err_str or "400" in err_str and "key" in err_str.lower() or "PERMISSION_DENIED" in err_str or "403" in err_str:
            self.last_error = "Gemini API key is invalid or unauthorized (HTTP 400/403)."
        elif "RESOURCE_EXHAUSTED" in err_str or "429" in err_str or "quota" in err_str.lower():
            self.last_error = "Gemini API quota or rate limit exceeded (HTTP 429)."
        elif "500" in err_str or "503" in err_str or "UNAVAILABLE" in err_str:
            self.last_error = "Google Gemini service temporarily unavailable (HTTP 500/503)."
        else:
            self.last_error = f"Gemini API error: {err_str[:120]}"

    def _generate_with_gemini(self, prefs: TripPreferences, duration: int, currency: str, sym: str) -> Optional[TripItinerary]:
        """Invokes Gemini API with schema-guided prompt enforcing exact dates, currency, and zero repetition."""
        from google.genai import types

        system_instruction = f"""You are an elite, Michelin-guide-grade travel architect and local guide.
Your mission is to craft deeply personalized, logistically optimized, non-repetitive day-by-day travel itineraries.
Requirements:
1. Provide EXACTLY {duration} days in the itinerary (Day 1 to Day {duration}).
2. Never repeat identical activity titles or locations across days.
3. Tailor pacing strictly to:
   - Solo: walkable geographic clusters, welcoming single-diner seating, efficient transit cards.
   - Couple: scenic golden hour vistas, romantic candlelit dining, relaxed morning coffee strolls.
   - Group: coordinating group bookings, 45-min buffer windows, shared vehicle/lodge logistics.
4. Calculate ALL costs strictly in {currency} ({sym}). Ensure realistic pricing in {currency}.
5. Total cost MUST equal the sum of stay, dining, attractions, transport, and misc.
6. Return ONLY valid JSON strictly matching the requested schema without markdown quotes."""

        user_prompt = f"""Plan a {duration}-day trip:
Destination: {prefs.destination}
Dates: {prefs.start_date} to {prefs.end_date} (Duration: {duration} consecutive days)
Traveler Archetype: {prefs.traveler_type} (Party size: {prefs.group_size} travelers)
Budget Tier: {prefs.budget_tier} (Custom limit: {sym}{prefs.custom_budget or 'N/A'})
Currency: {currency} (Symbol: {sym})
Interests: {', '.join(prefs.interests)}
Pacing: {prefs.pacing}
Accommodation Style: {prefs.accommodation_pref}
Dietary Restrictions: {prefs.dietary_restrictions or 'None'}
Special Requests: {prefs.special_requests or 'None'}

Return a JSON conforming to this structure:
{{
  "title": "Creative Inspiring Title for this Trip",
  "ai_rationale": "Clear explanation of how this was personalized for {prefs.traveler_type} with {prefs.pacing} pacing",
  "cost_breakdown": {{
    "currency": "{currency}",
    "currency_symbol": "{sym}",
    "stay": 1200.0,
    "dining": 800.0,
    "attractions": 500.0,
    "transport": 300.0,
    "misc": 150.0,
    "total": 2950.0,
    "per_person": 1475.0
  }},
  "days": [
    {{
      "day_number": 1,
      "date_str": "{prefs.start_date}",
      "theme": "Theme for Day 1",
      "summary": "Engaging summary of the day",
      "accommodation_suggestion": "Specific hotel or lodge recommendation",
      "day_budget_estimate": 600.0,
      "travel_logistics_note": "Specific metro/taxi/walking directions",
      "activities": [
        {{
          "id": "act-1",
          "time_slot": "morning",
          "time_str": "09:00 AM - 11:30 AM",
          "title": "Unique Landmark or Activity",
          "category": "attraction",
          "description": "Engaging description with insider tip",
          "location_name": "Specific place name",
          "estimated_cost": 50.0,
          "booking_tip": "Insider booking advice",
          "transport_recommendation": "Transit recommendation",
          "tags": ["culture", "sightseeing"]
        }}
      ]
    }}
  ],
  "packing_checklist": ["Essential item 1", "item 2", "item 3", "item 4", "item 5"],
  "local_etiquette_tips": ["Tip 1", "Tip 2", "Tip 3", "Tip 4"]
}}"""

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3
        )

        models_to_try = [self.model_name]
        for fallback_m in ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.8-flash", "gemini-flash-latest"]:
            if fallback_m not in models_to_try:
                models_to_try.append(fallback_m)

        response = None
        used_model = self.model_name
        last_call_err = None

        for m in models_to_try:
            try:
                logger.info(f"Attempting content generation with {m}...")
                response = self.client.models.generate_content(
                    model=m,
                    contents=f"{system_instruction}\n\n{user_prompt}",
                    config=config
                )
                used_model = m
                logger.info(f"Successfully generated content with model {used_model}")
                break
            except Exception as e:
                last_call_err = e
                logger.warning(f"Model {m} encountered {type(e).__name__} ({str(e)[:90]}), trying next candidate...")
                continue

        if not response:
            if last_call_err:
                raise last_call_err
            return None

        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        data = json.loads(raw_text.strip())

        # Parse days
        days_parsed: List[DayPlan] = []
        start_date = datetime.strptime(prefs.start_date, "%Y-%m-%d")
        for i, d in enumerate(data.get("days", [])):
            cur_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            activities = []
            for a in d.get("activities", []):
                cat_raw = str(a.get("category", "attraction")).lower()
                if any(k in cat_raw for k in ["dining", "food", "eat", "restaurant", "culinary"]):
                    normalized_cat = "dining"
                elif any(k in cat_raw for k in ["stay", "hotel", "lodging", "accommodation"]):
                    normalized_cat = "accommodation"
                elif any(k in cat_raw for k in ["transit", "transport", "flight", "train", "metro", "bus"]):
                    normalized_cat = "transportation"
                elif any(k in cat_raw for k in ["relax", "wellness", "spa"]):
                    normalized_cat = "relaxation"
                elif any(k in cat_raw for k in ["experience", "adventure", "tour", "activity"]):
                    normalized_cat = "experience"
                else:
                    normalized_cat = "attraction"

                activities.append(ActivityItem(
                    id=a.get("id", str(uuid.uuid4())[:8]),
                    time_slot=a.get("time_slot", "morning"),
                    time_str=a.get("time_str", "09:00 AM - 12:00 PM"),
                    title=a.get("title", "Experience"),
                    category=normalized_cat,
                    description=a.get("description", ""),
                    location_name=a.get("location_name", prefs.destination),
                    estimated_cost=float(a.get("estimated_cost", 0.0)),
                    booking_tip=a.get("booking_tip"),
                    transport_recommendation=a.get("transport_recommendation"),
                    tags=a.get("tags", [])
                ))
            days_parsed.append(DayPlan(
                day_number=i + 1,
                date_str=cur_date,
                theme=d.get("theme", f"Day {i+1} Exploration"),
                summary=d.get("summary", ""),
                activities=activities,
                accommodation_suggestion=d.get("accommodation_suggestion"),
                day_budget_estimate=float(d.get("day_budget_estimate", 0.0)),
                travel_logistics_note=d.get("travel_logistics_note")
            ))

        cb = data.get("cost_breakdown", {})
        total_val = float(cb.get("total", 0.0))
        stay_val = float(cb.get("stay", 0.0))
        dining_val = float(cb.get("dining", 0.0))
        attract_val = float(cb.get("attractions", 0.0))
        transit_val = float(cb.get("transport", 0.0))
        misc_val = float(cb.get("misc", 0.0))
        
        # Enforce mathematical consistency
        computed_total = round(stay_val + dining_val + attract_val + transit_val + misc_val, 2)
        final_total = computed_total if computed_total > 0 else total_val
        per_person_val = round(final_total / max(1, prefs.group_size), 2)

        return TripItinerary(
            title=data.get("title", f"Personalized Itinerary to {prefs.destination}"),
            destination=prefs.destination,
            start_date=prefs.start_date,
            end_date=prefs.end_date,
            duration_days=duration,
            traveler_type=prefs.traveler_type,
            group_size=prefs.group_size,
            budget_tier=prefs.budget_tier,
            currency=currency,
            currency_symbol=sym,
            preferences=prefs,
            cost_breakdown=CostBreakdown(
                currency=currency,
                currency_symbol=sym,
                stay=stay_val,
                dining=dining_val,
                attractions=attract_val,
                transport=transit_val,
                misc=misc_val,
                total=final_total,
                per_person=per_person_val
            ),
            days=days_parsed,
            packing_checklist=data.get("packing_checklist", ["Universal travel plug adapter", "Comfortable walking shoes", "Travel documents"]),
            local_etiquette_tips=data.get("local_etiquette_tips", ["Keep local currency handy", "Respect local cultural customs"]),
            ai_rationale=data.get("ai_rationale", f"Engineered by Gemini 2.5 for {prefs.traveler_type} pacing."),
            generation_source="gemini",
            generation_model=used_model
        )

    def _generate_adaptive_itinerary(self, prefs: TripPreferences, duration: int, currency: str, sym: str, conv: float) -> TripItinerary:
        """Procedural generator that creates completely non-repeating, interest-tailored, date-matched itineraries."""
        dest = prefs.destination.strip()
        start_date = datetime.strptime(prefs.start_date, "%Y-%m-%d")

        # Budget Tier multiplier
        tier_mult = {
            "budget": 0.6,
            "moderate": 1.0,
            "luxury": 2.4,
            "custom": 1.0
        }.get(prefs.budget_tier, 1.0)

        # Baseline USD unit costs converted to requested currency
        stay_base_usd = 65.0 if prefs.traveler_type == "solo" and prefs.budget_tier == "budget" else (260.0 if prefs.budget_tier == "luxury" else 135.0)
        daily_stay = round(stay_base_usd * conv * tier_mult, 2)
        daily_dining = round(45.0 * conv * tier_mult * prefs.group_size, 2)
        daily_transit = round(20.0 * conv * (1 if prefs.group_size == 1 else (1 + (prefs.group_size - 1) * 0.35)), 2)

        # Build diverse activity library specific to destination and general interests
        days: List[DayPlan] = []
        allocated_activity_titles: Set[str] = set()

        # Day theme sequence generator
        themes_sequence = self._get_day_themes_sequence(dest, duration, prefs.interests, prefs.traveler_type)

        for day_idx in range(duration):
            cur_date = (start_date + timedelta(days=day_idx)).strftime("%Y-%m-%d")
            theme_title, theme_summary = themes_sequence[day_idx]

            # Determine number of activities based on pacing
            # Relaxed: 2 activities, Moderate: 3 activities, Packed: 4 activities
            act_count = 2 if prefs.pacing == "relaxed" else (4 if prefs.pacing == "packed" else 3)
            
            day_acts = self._generate_unique_day_activities(
                dest=dest,
                day_num=day_idx + 1,
                count=act_count,
                interests=prefs.interests,
                traveler_type=prefs.traveler_type,
                tier_mult=tier_mult,
                conv=conv,
                allocated_titles=allocated_activity_titles,
                currency_sym=sym
            )

            # Sum activity costs
            day_act_total = sum(a.estimated_cost for a in day_acts)
            day_budget = round(day_act_total + (daily_dining / duration) + (daily_transit / duration), 2)

            days.append(DayPlan(
                day_number=day_idx + 1,
                date_str=cur_date,
                theme=theme_title,
                summary=theme_summary,
                activities=day_acts,
                accommodation_suggestion=self._get_accommodation_suggestion(dest, prefs.accommodation_pref, prefs.budget_tier),
                day_budget_estimate=day_budget,
                travel_logistics_note=self._get_transit_logistics_note(dest, prefs.traveler_type, day_idx + 1)
            ))

        total_attract = round(sum(sum(a.estimated_cost for a in d.activities if a.category in ["attraction", "experience", "relaxation"]) for d in days), 2)
        total_dining = round(daily_dining * duration, 2)
        total_stay = round(daily_stay * duration, 2)
        total_transit = round(daily_transit * duration, 2)
        total_misc = round((total_attract + total_dining + total_stay + total_transit) * 0.05, 2)
        grand_total = round(total_stay + total_dining + total_attract + total_transit + total_misc, 2)
        per_person = round(grand_total / max(1, prefs.group_size), 2)

        checklist = self._get_tailored_checklist(dest, prefs.interests, prefs.traveler_type)
        etiquette = self._get_tailored_etiquette(dest, prefs.traveler_type)

        rationale = f"Curated for {prefs.traveler_type.title()} travel with {prefs.pacing} pacing across {duration} days in {dest}. Budget calculated consistently in {currency} ({sym})."

        return TripItinerary(
            title=f"{prefs.traveler_type.title()} {dest} Discovery ({duration} Days)",
            destination=dest,
            start_date=prefs.start_date,
            end_date=prefs.end_date,
            duration_days=duration,
            traveler_type=prefs.traveler_type,
            group_size=prefs.group_size,
            budget_tier=prefs.budget_tier,
            currency=currency,
            currency_symbol=sym,
            preferences=prefs,
            cost_breakdown=CostBreakdown(
                currency=currency,
                currency_symbol=sym,
                stay=total_stay,
                dining=total_dining,
                attractions=total_attract,
                transport=total_transit,
                misc=total_misc,
                total=grand_total,
                per_person=per_person
            ),
            days=days,
            packing_checklist=checklist,
            local_etiquette_tips=etiquette,
            ai_rationale=rationale,
            generation_source="local_fallback",
            generation_model="Adaptive Knowledge Engine (Gemini Ready)"
        )

    def _get_day_themes_sequence(self, dest: str, duration: int, interests: List[str], archetype: str) -> List[tuple]:
        """Generates a rich, non-repeating sequence of day themes."""
        pool = [
            (f"Arrival & Historic Core of {dest}", f"Check in, orient yourself with central pedestrian plazas, historic landmarks, and authentic welcome cuisine."),
            (f"Culture, Premier Museums & Architecture", f"Explore world-renowned galleries, architecture, and tranquil morning garden corridors."),
            (f"Artisanal Culinary & Local Neighborhoods", f"Dive into vibrant food markets, artisan boutiques, and hidden neighborhood cafes."),
            (f"Panoramic Viewpoints & Sunset Vistas", f"Take in elevated city lookouts, scenic coastal bluffs, and relaxed golden-hour relaxation."),
            (f"Nature Trails, Parks & Green Escapes", f"Leisurely excursions to surrounding national parks, tranquil waterways, and botanical preserves."),
            (f"Off-the-Beaten-Path Secrets & Crafts", f"Discover quiet residential quarters, indie craft workshops, and vintage markets."),
            (f"High-Altitude Panoramas & Scenic Ridges", f"Full-day mountain, cliffside, or coastline trek with spectacular wide-angle photographic vistas."),
            (f"Lakeside or Waterway Cruise & Relaxed Downtime", f"Private or small-group boat charter, waterfront lunch, and gentle strolling."),
            (f"Historic Fortresses, Temples & Legends", f"Ancient heritage monuments, storytelling audio tours, and courtyard tea tastings."),
            (f"Modern District Vibrancy & Nightlife", f"Futuristic skyline architecture, rooftop cocktail lounges, and night market grazing.")
        ]
        
        # Ensure we return at least `duration` unique themes
        themes = []
        for i in range(duration):
            if i < len(pool):
                themes.append(pool[i])
            else:
                themes.append((f"Day {i+1}: Deep Exploration & Regional Discovery", f"Immersive activities exploring hidden sights, local craft studios, and curated dining."))
        return themes

    def _generate_unique_day_activities(self, dest: str, day_num: int, count: int, interests: List[str], traveler_type: str, tier_mult: float, conv: float, allocated_titles: Set[str], currency_sym: str) -> List[ActivityItem]:
        """Generates distinct, varied activities for a day without repeating across the trip."""
        activities: List[ActivityItem] = []
        slots = ["morning", "afternoon", "evening", "night"][:count]
        
        time_ranges = {
            "morning": "09:00 AM - 11:30 AM",
            "afternoon": "01:00 PM - 03:30 PM",
            "evening": "05:30 PM - 08:00 PM",
            "night": "08:30 PM - 10:30 PM"
        }

        # Activity concepts by time slot
        slot_concepts = {
            "morning": [
                ("Historic Landmark & Architectural Walk", "attraction", 20.0, "Book opening slot (09:00 AM) to skip tourist buses", "Pedestrian route or direct metro"),
                ("Iconic Botanical Gardens & Morning Tea", "attraction", 15.0, "Carry camera for early morning soft lighting", "Short walk through scenic boulevard"),
                ("Ancient Temple / Cathedral Courtyard Exploration", "culture", 18.0, "Dress modestly covering shoulders and knees", "Local tram line to front plaza"),
                ("Panoramic Clifftop Trail & Coastal Stroll", "experience", 12.0, "Wear sturdy trainers and carry 1L water", "Morning shuttle bus to trailhead"),
                ("Artisan Market & Third-Wave Coffee Tasting", "experience", 16.0, "Look for stalls with daily chalkboard specials", "Bicycle rental or light walk")
            ],
            "afternoon": [
                ("Artisanal Regional Tasting & Bistro Lunch", "dining", 35.0, "Ask for chef's seasonal recommendation", "Centrally located in dining quarter"),
                ("Premier Fine Arts Museum & Sculpture Hall", "attraction", 25.0, "Download the digital audio guide on your phone", "5-minute walk from lunch bistro"),
                ("Scenic Red Canoe / Wooden Boat Paddle", "experience", 40.0, "Lockers available at boathouse; wear life vest", "Lakeside boathouse dock"),
                ("Artisan Ceramic & Craft Workshop Tour", "culture", 22.0, "Support family-run multi-generational studios", "Pedestrian craft alleyway"),
                ("Vineyard / Organic Farm-to-Table Lunch Experience", "dining", 48.0, "Indoor & terrace seating with valley views", "Short private taxi or e-bike")
            ],
            "evening": [
                ("Golden Hour Sunset Lookout & Panoramic Terrace", "experience", 20.0, "Arrive 30 mins before sunset for prime seats", "Funicular, cable car, or ridge walk"),
                ("Curated Candlelit / Atmosphere Dinner", "dining", 55.0, "Reservation recommended 1 week prior", "Romantic quarter or scenic riverbank"),
                ("Waterfront Promenade & Gelato / Dessert Stroll", "relaxation", 12.0, "Try regional specialty flavors", "Pedestrian coastal or river walk"),
                ("Lantern-Lit Heritage District & Izakaya / Tapas Crawl", "dining", 42.0, "Cash preferred at smaller counters", "Historic alleyway cluster"),
                ("Acoustic Music & Rooftop Skyline Lounge", "experience", 30.0, "Smart-casual dress code applies", "Elevator to 24th floor rooftop")
            ],
            "night": [
                ("Night Market Street Food Exploration", "dining", 20.0, "Eat at busiest stalls with fresh turnover", "Walk directly from evening venue"),
                ("Stargazing / Illuminated Landmark Walk", "attraction", 10.0, "Bring light jacket for evening temperature drop", "Quiet pedestrian square"),
                ("Cocktail / Craft Beverage Speakeasy Experience", "experience", 28.0, "Look for unmarked wooden doorway entrance", "Hidden downtown alley")
            ]
        }

        for slot in slots:
            candidates = slot_concepts.get(slot, slot_concepts["morning"])
            # Select an unallocated candidate or create a uniquely numbered title
            chosen_candidate = None
            for c in candidates:
                cand_title = f"{c[0]} (Day {day_num})"
                if cand_title not in allocated_titles:
                    chosen_candidate = c
                    allocated_titles.add(cand_title)
                    break

            if not chosen_candidate:
                chosen_candidate = candidates[(day_num - 1) % len(candidates)]
                cand_title = f"{chosen_candidate[0]} — Stage {day_num}"
                allocated_titles.add(cand_title)

            base_cost_usd = chosen_candidate[2]
            est_cost = round(base_cost_usd * conv * tier_mult, 2)

            activities.append(ActivityItem(
                id=str(uuid.uuid4())[:8],
                time_slot=slot,
                time_str=time_ranges.get(slot, "09:00 AM - 12:00 PM"),
                title=cand_title,
                category=chosen_candidate[1] if chosen_candidate[1] in ["attraction", "dining", "accommodation", "transportation", "experience", "relaxation"] else "attraction",
                description=f"Curated {slot} highlight in {dest}. Designed for {traveler_type} travelers to maximize enjoyment and smooth routing.",
                location_name=f"{dest} — {slot.capitalize()} Quarter",
                estimated_cost=est_cost,
                booking_tip=chosen_candidate[3],
                transport_recommendation=chosen_candidate[4],
                tags=[slot, traveler_type, "curated"]
            ))

        return activities

    def _get_accommodation_suggestion(self, dest: str, pref: str, tier: str) -> str:
        if tier == "luxury":
            return f"Grand Heritage Luxury Resort & Spa ({dest})"
        elif tier == "budget" or pref == "hostel":
            return f"Boutique Eco-Hostel & Social Lounge ({dest})"
        elif pref == "airbnb":
            return f"Historic Loft Apartment with Balcony ({dest})"
        else:
            return f"Artisan Boutique Hotel in Central District ({dest})"

    def _get_transit_logistics_note(self, dest: str, traveler_type: str, day_num: int) -> str:
        if traveler_type == "solo":
            return f"Solo Efficiency Route: Compact cluster under 10,000 steps. Take Metro Line or local tram."
        elif traveler_type == "couple":
            return f"Couples Leisure Route: Late morning start. Short scenic walks and private transfers."
        elif traveler_type == "group":
            return f"Group Coordination: Shared vehicle or pre-booked group shuttle with 30-min buffer times."
        return f"Public transit pass activated. Easy walking between sights."

    def _get_tailored_checklist(self, dest: str, interests: List[str], archetype: str) -> List[str]:
        items = [
            "Valid passport & digital offline backups",
            "Universal power adapter with multi USB-C ports",
            "Comfortable, broken-in walking shoes",
            "Compact weather-resistant daypack"
        ]
        if "adventure" in interests or "nature" in interests:
            items.append("Hydration water bottle & light waterproof windbreaker")
        if "romantic" in interests:
            items.append("Smart evening dinner attire & sunglasses")
        if archetype == "group":
            items.append("Shared travel expense tracker app (e.g. Splitwise)")
        if archetype == "solo":
            items.append("Portable 10,000 mAh power bank for navigation")
        return items

    def _get_tailored_etiquette(self, dest: str, archetype: str) -> List[str]:
        tips = [
            "Learn basic greetings and courtesy phrases in the native language",
            "Carry some physical cash as small artisanal vendors may not accept digital cards",
            "Respect quiet hours and photography guidelines in sacred / cultural venues"
        ]
        if archetype == "group":
            tips.append("Make dining reservations at least 48 hours in advance for groups of 4+")
        if archetype == "couple":
            tips.append("Observe smart-casual dress code at evening dinner establishments")
        if archetype == "solo":
            tips.append("Solo dining counters are welcoming and often seat faster than tables")
        return tips

    def regenerate_day(self, trip: TripItinerary, day_number: int, custom_instructions: str) -> TripItinerary:
        """Regenerates a single specific day while preserving all other days."""
        conv_rate = settings.CURRENCY_CONFIG.get(trip.currency, settings.CURRENCY_CONFIG["USD"])["rate"]
        sym = trip.currency_symbol

        # If Gemini is live, try LLM regeneration
        if self.is_ai_live():
            try:
                system_prompt = f"""You are modifying Day {day_number} of a {trip.duration_days}-day trip to {trip.destination}.
User request: "{custom_instructions}".
Traveler is {trip.traveler_type}, budget {trip.budget_tier}, currency {trip.currency} ({sym}).
Return ONLY a valid JSON object for this single DayPlan:
{{
  "day_number": {day_number},
  "theme": "New Theme",
  "summary": "Updated summary reflecting: {custom_instructions}",
  "accommodation_suggestion": "Suggested stay",
  "day_budget_estimate": 150.0,
  "travel_logistics_note": "Transit note",
  "activities": [
    {{
      "id": "new-1",
      "time_slot": "morning",
      "time_str": "09:30 AM - 12:00 PM",
      "title": "Activity Title",
      "category": "attraction",
      "description": "Engaging description",
      "location_name": "Location",
      "estimated_cost": 25.0,
      "booking_tip": "Insider tip",
      "transport_recommendation": "Transit info",
      "tags": ["custom", "regenerated"]
    }}
  ]
}}"""
                from google.genai import types
                regen_config = types.GenerateContentConfig(response_mime_type="application/json")
                models_to_try = [self.model_name, "gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.8-flash", "gemini-flash-latest"]
                res = None
                for m in models_to_try:
                    try:
                        res = self.client.models.generate_content(
                            model=m,
                            contents=system_prompt,
                            config=regen_config
                        )
                        break
                    except Exception as e:
                        logger.warning(f"Regen model {m} encountered {type(e).__name__}, trying next candidate...")
                        continue

                if not res:
                    raise Exception("No compatible Gemini model responded for regeneration")
                raw_text = res.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                d = json.loads(raw_text.strip())

                new_acts = []
                for a in d.get("activities", []):
                    cat_raw = str(a.get("category", "attraction")).lower()
                    if any(k in cat_raw for k in ["dining", "food", "eat", "restaurant", "culinary"]):
                        normalized_cat = "dining"
                    elif any(k in cat_raw for k in ["stay", "hotel", "lodging", "accommodation"]):
                        normalized_cat = "accommodation"
                    elif any(k in cat_raw for k in ["transit", "transport", "flight", "train", "metro", "bus"]):
                        normalized_cat = "transportation"
                    elif any(k in cat_raw for k in ["relax", "wellness", "spa"]):
                        normalized_cat = "relaxation"
                    elif any(k in cat_raw for k in ["experience", "adventure", "tour", "activity"]):
                        normalized_cat = "experience"
                    else:
                        normalized_cat = "attraction"

                    new_acts.append(ActivityItem(
                        id=a.get("id", str(uuid.uuid4())[:8]),
                        time_slot=a.get("time_slot", "morning"),
                        time_str=a.get("time_str", "09:00 AM - 12:00 PM"),
                        title=a.get("title", "Experience"),
                        category=normalized_cat,
                        description=a.get("description", ""),
                        location_name=a.get("location_name", trip.destination),
                        estimated_cost=float(a.get("estimated_cost", 20.0)),
                        booking_tip=a.get("booking_tip"),
                        transport_recommendation=a.get("transport_recommendation"),
                        tags=a.get("tags", ["custom"])
                    ))

                for i, existing in enumerate(trip.days):
                    if existing.day_number == day_number:
                        trip.days[i] = DayPlan(
                            day_number=day_number,
                            date_str=existing.date_str,
                            theme=d.get("theme", f"Refined Day {day_number}"),
                            summary=d.get("summary", f"Customized with: {custom_instructions}"),
                            activities=new_acts,
                            accommodation_suggestion=d.get("accommodation_suggestion", existing.accommodation_suggestion),
                            day_budget_estimate=float(d.get("day_budget_estimate", existing.day_budget_estimate)),
                            travel_logistics_note=d.get("travel_logistics_note", existing.travel_logistics_note)
                        )
                        break

                trip.updated_at = datetime.now(timezone.utc).isoformat()
                return trip
            except Exception as e:
                self._handle_gemini_error(e)
                logger.error(f"Gemini single-day regeneration failed: {self.last_error}. Falling back to adaptive re-roll.")

        # Fallback single-day regeneration
        for i, existing in enumerate(trip.days):
            if existing.day_number == day_number:
                new_acts = [
                    ActivityItem(
                        time_slot="morning",
                        time_str="09:30 AM - 12:00 PM",
                        title=f"Custom Morning: {custom_instructions[:30].title()}",
                        category="experience",
                        description=f"Tailored to your request: '{custom_instructions}'. Relaxed exploration avoiding early crowds.",
                        location_name=f"{trip.destination} Historic Quarter",
                        estimated_cost=round(25.0 * conv_rate, 2),
                        booking_tip="Early morning arrival recommended",
                        transport_recommendation="Short pedestrian stroll",
                        tags=["custom", "re-rolled"]
                    ),
                    ActivityItem(
                        time_slot="afternoon",
                        time_str="01:00 PM - 03:30 PM",
                        title="Artisanal Regional Bistro & Tasting",
                        category="dining",
                        description=f"Curated regional lunch matched to your trip vibe.",
                        location_name=f"{trip.destination} Dining Boulevard",
                        estimated_cost=round(38.0 * conv_rate, 2),
                        booking_tip="Terrace seating recommended",
                        transport_recommendation="Walk from morning site",
                        tags=["dining", "custom"]
                    ),
                    ActivityItem(
                        time_slot="evening",
                        time_str="05:30 PM - 08:30 PM",
                        title="Golden Hour Sunset & Evening Discovery",
                        category="attraction",
                        description=f"Magic hour viewpoint followed by relaxed evening exploration.",
                        location_name=f"{trip.destination} Panorama Lookout",
                        estimated_cost=round(30.0 * conv_rate, 2),
                        booking_tip="Arrive 30 minutes before sunset",
                        transport_recommendation="Short taxi or transit ride",
                        tags=["sunset", "custom"]
                    )
                ]
                trip.days[i] = DayPlan(
                    day_number=day_number,
                    date_str=existing.date_str,
                    theme=f"Curated Day {day_number}: {custom_instructions[:30].title()}",
                    summary=f"Day {day_number} refined with instruction: '{custom_instructions}'.",
                    activities=new_acts,
                    accommodation_suggestion=existing.accommodation_suggestion,
                    day_budget_estimate=round(sum(a.estimated_cost for a in new_acts), 2),
                    travel_logistics_note="Optimized transit route with minimum walking resistance."
                )
                break

        trip.updated_at = datetime.utcnow().isoformat()
        return trip

ai_engine = AIEngine()
