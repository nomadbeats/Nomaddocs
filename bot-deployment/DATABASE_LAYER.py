"""
Database abstraction layer for Supabase
Handles all database operations
"""

from supabase import create_client, Client
from typing import Dict, List, Any, Optional
import json
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations with Supabase"""
    
    def __init__(self):
        """Initialize Supabase connection"""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        
        self.client: Client = create_client(self.url, self.key)
    
    # ===== CONFIG =====
    def get_config(self) -> Dict[str, Any]:
        """Get bot configuration"""
        try:
            response = self.client.table("config").select("*").execute()
            config = {}
            for item in response.data:
                config[item['key']] = item['value']
            return config
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return {}
    
    def set_config(self, key: str, value: str) -> bool:
        """Set configuration value"""
        try:
            self.client.table("config").update({"value": value}).eq("key", key).execute()
            return True
        except:
            self.client.table("config").insert({"key": key, "value": value}).execute()
            return True
    
    # ===== PAGES =====
    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get single page"""
        try:
            response = self.client.table("pages").select("*").eq("page_id", page_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting page {page_id}: {e}")
            return None
    
    def get_all_pages(self) -> Dict[str, Any]:
        """Get all pages"""
        try:
            response = self.client.table("pages").select("*").execute()
            pages = {}
            for page in response.data:
                pages[page['page_id']] = page
            return pages
        except Exception as e:
            logger.error(f"Error getting pages: {e}")
            return {}
    
    def create_page(self, page_id: str, title: str, text: str) -> bool:
        """Create new page"""
        try:
            self.client.table("pages").insert({
                "page_id": page_id,
                "title": title,
                "text": text,
                "buttons": "[]",
                "tags": "[]",
                "access": "public"
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error creating page: {e}")
            return False
    
    def update_page(self, page_id: str, updates: Dict[str, Any]) -> bool:
        """Update page"""
        try:
            self.client.table("pages").update(updates).eq("page_id", page_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating page: {e}")
            return False
    
    def delete_page(self, page_id: str) -> bool:
        """Delete page"""
        try:
            self.client.table("pages").delete().eq("page_id", page_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting page: {e}")
            return False
    
    # ===== USERS =====
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data"""
        try:
            response = self.client.table("users").select("*").eq("user_id", user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def create_user(self, user_id: int, username: str) -> bool:
        """Create new user"""
        try:
            self.client.table("users").insert({
                "user_id": user_id,
                "username": username,
                "pages_visited": "[]",
                "buttons_clicked": "[]",
                "xp": 0,
                "badges": "[]",
                "bookmarks": "[]",
                "donated": False,
                "donation_amount": 0
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            self.client.table("users").update(updates).eq("user_id", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    # ===== DONATIONS =====
    def add_donation(self, user_id: int, amount: int, username: str, payload: str) -> bool:
        """Record donation"""
        try:
            self.client.table("donations").insert({
                "user_id": user_id,
                "amount": amount,
                "username": username,
                "payload": payload
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error adding donation: {e}")
            return False
    
    def get_donations(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get donations"""
        try:
            query = self.client.table("donations").select("*")
            if user_id:
                query = query.eq("user_id", user_id)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting donations: {e}")
            return []
    
    # ===== STATISTICS =====
    def get_stat(self, key: str) -> str:
        """Get statistic value"""
        try:
            response = self.client.table("statistics").select("stat_value").eq("stat_key", key).execute()
            if response.data:
                return response.data[0]['stat_value']
            return "0"
        except Exception as e:
            logger.error(f"Error getting stat {key}: {e}")
            return "0"
    
    def set_stat(self, key: str, value: str) -> bool:
        """Set statistic value"""
        try:
            self.client.table("statistics").update({"stat_value": value}).eq("stat_key", key).execute()
            return True
        except:
            self.client.table("statistics").insert({"stat_key": key, "stat_value": value}).execute()
            return True
    
    # ===== GENERAL HELPERS =====
    def json_to_db(self, data: Any) -> str:
        """Convert JSON to string for storage"""
        return json.dumps(data)
    
    def db_to_json(self, data: str) -> Any:
        """Convert stored string back to JSON"""
        try:
            return json.loads(data) if isinstance(data, str) else data
        except:
            return {}

# Global instance
db = None

def get_db() -> DatabaseManager:
    """Get database manager instance"""
    global db
    if db is None:
        db = DatabaseManager()
    return db
