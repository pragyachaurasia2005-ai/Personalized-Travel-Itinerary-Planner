import sqlite3
import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from .config import settings
from .supabase_service import supabase_service

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, db_path: Path = settings.DB_PATH):
        self.db_path = db_path
        self._init_sqlite()

    def _init_sqlite(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    traveler_type TEXT NOT NULL,
                    group_size INTEGER DEFAULT 1,
                    budget_tier TEXT NOT NULL,
                    total_estimated_cost_usd REAL DEFAULT 0.0,
                    currency TEXT DEFAULT 'USD',
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

            # Check for currency column migration if table already existed
            cursor.execute("PRAGMA table_info(trips)")
            cols = [info[1] for info in cursor.fetchall()]
            if "currency" not in cols:
                cursor.execute("ALTER TABLE trips ADD COLUMN currency TEXT DEFAULT 'USD'")
                conn.commit()

            conn.close()
        except Exception as e:
            logger.error(f"Error initializing SQLite database: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Provides a completely truthful report of active storage mode."""
        sb_connected = supabase_service.check_connection()
        sb_details = supabase_service.get_status_details()

        if sb_connected:
            mode_label = "Supabase Cloud (Active Primary)"
            primary_system = "supabase"
        elif sb_details["configured"]:
            mode_label = f"Local SQLite (Supabase Error: {sb_details['error']})"
            primary_system = "sqlite"
        else:
            mode_label = "Local SQLite Storage (Supabase Not Configured)"
            primary_system = "sqlite"

        return {
            "storage_mode": mode_label,
            "primary": primary_system,
            "supabase_configured": sb_details["configured"],
            "supabase_connected": sb_connected,
            "supabase_details": sb_details,
            "local_sqlite_active": True,
            "sqlite_file": str(self.db_path.name)
        }

    def save_trip(self, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        trip_id = str(trip_data["id"])
        
        # If Supabase is connected, save to Supabase as primary cloud store
        if supabase_service.is_connected():
            supabase_service.save_trip(trip_data)

        # Always maintain local SQLite cache / fallback
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO trips 
                (id, title, destination, start_date, end_date, duration_days, traveler_type, group_size, budget_tier, total_estimated_cost_usd, currency, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trip_id,
                trip_data.get("title", "Untitled Trip"),
                trip_data.get("destination", ""),
                trip_data.get("start_date", ""),
                trip_data.get("end_date", ""),
                trip_data.get("duration_days", 1),
                trip_data.get("traveler_type", "solo"),
                trip_data.get("group_size", 1),
                trip_data.get("budget_tier", "moderate"),
                trip_data.get("cost_breakdown", {}).get("total", 0.0),
                trip_data.get("currency", "USD"),
                json.dumps(trip_data),
                trip_data.get("created_at", ""),
                trip_data.get("updated_at", "")
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"SQLite save_trip error: {e}")

        return trip_data

    def get_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        # Check Supabase first if active
        if supabase_service.is_connected():
            sb_trip = supabase_service.get_trip(trip_id)
            if sb_trip:
                return sb_trip

        # SQLite query fallback
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT data_json FROM trips WHERE id = ?", (trip_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return json.loads(row[0])
            return None
        except Exception as e:
            logger.error(f"SQLite get_trip error: {e}")
            return None

    def list_trips(self, search: Optional[str] = None, traveler_type: Optional[str] = None) -> List[Dict[str, Any]]:
        # If Supabase is connected, retrieve from Supabase primary cloud
        if supabase_service.is_connected():
            sb_trips = supabase_service.list_trips()
            if sb_trips:
                filtered = []
                for item in sb_trips:
                    if search:
                        s_lower = search.lower()
                        if s_lower not in item.get("destination", "").lower() and s_lower not in item.get("title", "").lower():
                            continue
                    if traveler_type and item.get("traveler_type") != traveler_type:
                        continue
                    filtered.append(item)
                return filtered

        # SQLite fallback list
        results = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT data_json FROM trips ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            conn.close()
            for r in rows:
                item = json.loads(r[0])
                if search:
                    s_lower = search.lower()
                    if s_lower not in item.get("destination", "").lower() and s_lower not in item.get("title", "").lower():
                        continue
                if traveler_type and item.get("traveler_type") != traveler_type:
                    continue
                results.append(item)
        except Exception as e:
            logger.error(f"SQLite list_trips error: {e}")

        return results

    def update_trip(self, trip_id: str, updated_trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates trip across primary (Supabase) and local SQLite fallback."""
        if supabase_service.is_connected():
            supabase_service.save_trip(updated_trip_data)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE trips SET 
                    title = ?,
                    total_estimated_cost_usd = ?,
                    data_json = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                updated_trip_data.get("title", "Untitled Trip"),
                updated_trip_data.get("cost_breakdown", {}).get("total", 0.0),
                json.dumps(updated_trip_data),
                updated_trip_data.get("updated_at", ""),
                trip_id
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"SQLite update_trip error: {e}")

        return updated_trip_data

    def delete_trip(self, trip_id: str) -> bool:
        deleted = False
        if supabase_service.is_connected():
            supabase_service.delete_trip(trip_id)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
        except Exception as e:
            logger.error(f"SQLite delete_trip error: {e}")

        return deleted

storage = StorageManager()
