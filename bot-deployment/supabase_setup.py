"""
Supabase Database Setup
Initializes all required tables and schema
"""

from supabase import create_client, Client
import os
import json

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def init_supabase() -> Client:
    """Initialize Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def create_tables(supabase: Client):
    """Create all required tables"""
    
    # 1. CONFIG TABLE
    supabase.table("config").insert({
        "key": "bot_token",
        "value": os.getenv("BOT_TOKEN", ""),
        "created_at": "now()"
    }).execute()
    
    print("✅ Created config table")
    
    # 2. PAGES TABLE
    supabase.table("pages").insert({
        "page_id": "home",
        "title": "Home",
        "text": "Welcome to our bot!",
        "buttons": "[]",
        "media_id": None,
        "tags": "[]",
        "protected": False,
        "access": "public",
        "created_at": "now()",
        "updated_at": "now()"
    }).execute()
    
    print("✅ Created pages table")
    
    # 3. USERS TABLE
    supabase.table("users").insert({
        "user_id": 0,
        "username": "system",
        "first_seen": "now()",
        "last_seen": "now()",
        "pages_visited": "[]",
        "buttons_clicked": "[]",
        "xp": 0,
        "badges": "[]",
        "bookmarks": "[]",
        "donated": False,
        "donation_amount": 0
    }).execute()
    
    print("✅ Created users table")
    
    # 4. DONATIONS TABLE
    supabase.table("donations").insert({
        "user_id": 0,
        "amount": 0,
        "username": "system",
        "donation_date": "now()",
        "payload": ""
    }).execute()
    
    print("✅ Created donations table")
    
    # 5. STATISTICS TABLE
    supabase.table("statistics").insert({
        "stat_key": "total_stars",
        "stat_value": "0",
        "updated_at": "now()"
    }).execute()
    
    print("✅ Created statistics table")
    
    # 6. BROADCASTS TABLE
    supabase.table("broadcasts").insert({
        "broadcast_id": "default",
        "message": "Welcome!",
        "users_sent": "[]",
        "sent_date": "now()"
    }).execute()
    
    print("✅ Created broadcasts table")
    
    print("\n✅ All tables created successfully!")

if __name__ == "__main__":
    supabase = init_supabase()
    create_tables(supabase)
    print("\n🎉 Supabase setup complete!")
