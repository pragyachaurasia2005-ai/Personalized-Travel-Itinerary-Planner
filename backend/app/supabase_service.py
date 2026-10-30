import logging
from typing import Optional, List, Dict, Any
from .config import settings, reload_environment

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self.client = None
        self._connected = False
        self._connection_error = None
        self.check_connection()

    def check_connection(self) -> bool:
        """Attempts a real ping/query to Supabase to verify connectivity truthfully."""
        reload_environment()
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_KEY

        if not url or not key:
            self.client = None
            self._connected = False
            self._connection_error = "Supabase URL or Key not set in environment"
            return False

        try:
            from supabase import create_client, Client
            self.client: Client = create_client(url, key)
            # Perform a test query against 'trips' table to confirm credentials and schema
            test_res = self.client.table("trips").select("id").limit(1).execute()
            self._connected = True
            self._connection_error = None
            logger.info("Supabase connected and verified successfully.")
            return True
        except Exception as e:
            err_msg = str(e)
            logger.warning(f"Supabase connection check failed: {err_msg}")
            self._connected = False
            self._connection_error = err_msg
            return False

    def is_configured(self) -> bool:
        return bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)

    def is_connected(self) -> bool:
        return self._connected and self.client is not None

    def get_status_details(self) -> Dict[str, Any]:
        return {
            "configured": self.is_configured(),
            "connected": self.is_connected(),
            "error": self._connection_error if not self.is_connected() else None,
            "url_preview": (settings.SUPABASE_URL[:20] + "...") if settings.SUPABASE_URL else None
        }

    def save_trip(self, trip_data: Dict[str, Any]) -> bool:
        if not self.is_connected():
            return False
        try:
            # Map model data to Supabase table
            payload = {
                "id": str(trip_data["id"]),
                "title": trip_data.get("title", "Untitled Trip"),
                "destination": trip_data.get("destination", ""),
                "start_date": trip_data.get("start_date", ""),
                "end_date": trip_data.get("end_date", ""),
                "duration_days": trip_data.get("duration_days", 1),
                "traveler_type": trip_data.get("traveler_type", "solo"),
                "group_size": trip_data.get("group_size", 1),
                "budget_tier": trip_data.get("budget_tier", "moderate"),
                "total_estimated_cost_usd": trip_data.get("cost_breakdown", {}).get("total", 0.0),
                "preferences": trip_data.get("preferences", {}),
                "cost_breakdown": trip_data.get("cost_breakdown", {}),
                "days": trip_data.get("days", []),
                "packing_checklist": trip_data.get("packing_checklist", []),
                "local_etiquette_tips": trip_data.get("local_etiquette_tips", []),
                "ai_rationale": trip_data.get("ai_rationale", ""),
                "is_saved": True,
                "created_at": trip_data.get("created_at"),
                "updated_at": trip_data.get("updated_at")
            }
            res = self.client.table("trips").upsert(payload).execute()
            return bool(res.data)
        except Exception as e:
            logger.error(f"Supabase save_trip error: {e}")
            return False

    def get_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected():
            return None
        try:
            res = self.client.table("trips").select("*").eq("id", trip_id).execute()
            if res.data and len(res.data) > 0:
                raw = res.data[0]
                # Reconstitute into TripItinerary structure
                return {
                    "id": raw["id"],
                    "title": raw["title"],
                    "destination": raw["destination"],
                    "start_date": str(raw["start_date"]),
                    "end_date": str(raw["end_date"]),
                    "duration_days": raw["duration_days"],
                    "traveler_type": raw["traveler_type"],
                    "group_size": raw.get("group_size", 1),
                    "budget_tier": raw["budget_tier"],
                    "currency": raw.get("cost_breakdown", {}).get("currency", "USD"),
                    "currency_symbol": raw.get("cost_breakdown", {}).get("currency_symbol", "$"),
                    "preferences": raw.get("preferences", {}),
                    "cost_breakdown": raw.get("cost_breakdown", {}),
                    "days": raw.get("days", []),
                    "packing_checklist": raw.get("packing_checklist", []),
                    "local_etiquette_tips": raw.get("local_etiquette_tips", []),
                    "ai_rationale": raw.get("ai_rationale", ""),
                    "generation_source": raw.get("generation_source", "local_fallback"),
                    "generation_model": raw.get("generation_model", "Supabase Cloud DB"),
                    "is_saved": True,
                    "created_at": str(raw.get("created_at")),
                    "updated_at": str(raw.get("updated_at"))
                }
            return None
        except Exception as e:
            logger.error(f"Supabase get_trip error: {e}")
            return None

    def list_trips(self) -> List[Dict[str, Any]]:
        if not self.is_connected():
            return []
        try:
            res = self.client.table("trips").select("*").order("updated_at", desc=True).execute()
            results = []
            for raw in (res.data or []):
                results.append({
                    "id": raw["id"],
                    "title": raw["title"],
                    "destination": raw["destination"],
                    "start_date": str(raw["start_date"]),
                    "end_date": str(raw["end_date"]),
                    "duration_days": raw["duration_days"],
                    "traveler_type": raw["traveler_type"],
                    "group_size": raw.get("group_size", 1),
                    "budget_tier": raw["budget_tier"],
                    "currency": raw.get("cost_breakdown", {}).get("currency", "USD"),
                    "currency_symbol": raw.get("cost_breakdown", {}).get("currency_symbol", "$"),
                    "preferences": raw.get("preferences", {}),
                    "cost_breakdown": raw.get("cost_breakdown", {}),
                    "days": raw.get("days", []),
                    "packing_checklist": raw.get("packing_checklist", []),
                    "local_etiquette_tips": raw.get("local_etiquette_tips", []),
                    "ai_rationale": raw.get("ai_rationale", ""),
                    "is_saved": True,
                    "created_at": str(raw.get("created_at")),
                    "updated_at": str(raw.get("updated_at"))
                })
            return results
        except Exception as e:
            logger.error(f"Supabase list_trips error: {e}")
            return []

    def update_trip(self, trip_id: str, updates: Dict[str, Any]) -> bool:
        if not self.is_connected():
            return False
        try:
            res = self.client.table("trips").update(updates).eq("id", trip_id).execute()
            return bool(res.data)
        except Exception as e:
            logger.error(f"Supabase update_trip error: {e}")
            return False

    def delete_trip(self, trip_id: str) -> bool:
        if not self.is_connected():
            return False
        try:
            res = self.client.table("trips").delete().eq("id", trip_id).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase delete_trip error: {e}")
            return False

supabase_service = SupabaseService()
