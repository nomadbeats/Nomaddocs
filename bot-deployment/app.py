
"""
toh abhi ye final he jo banega banega ,isko advanced cms mtlb content management system kehte shayd"""

import telebot
import json
import os
import sys
import shutil
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable, Any
from collections import defaultdict
import time
from flask import Flask, request  # ← WEBHOOK SUPPORT FOR VERCEL

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION & DATA PATHS
# ============================================================================

DATA_DIR = 'data'
MEDIA_DIR = os.path.join(DATA_DIR, 'media')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
CONTENT_FILE = os.path.join(DATA_DIR, 'content.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
ANALYTICS_FILE = os.path.join(DATA_DIR, 'analytics.json')
VERSIONS_FILE = os.path.join(DATA_DIR, 'versions.json')
FEEDBACK_FILE = os.path.join(DATA_DIR, 'feedback.json')
BOOKMARKS_FILE = os.path.join(DATA_DIR, 'bookmarks.json')
STATISTICS_FILE = os.path.join(DATA_DIR, 'statistics.json')
DONATIONS_FILE = os.path.join(DATA_DIR, 'donations.json')
DONATE_CONFIG_FILE = os.path.join(DATA_DIR, 'donate_config.json')

# Log channel ID
LOG_CHANNEL_ID = -1002202841137

# ============================================================================
# QUOTES DATABASE
# ============================================================================

QUOTES: List[Tuple[str, str]] = [
    ("People die when they are killed.", "Fate/stay night"),
    ("I am the bone of my sword.", "Fate/stay night"),
    ("You should enjoy the little detours.", "Hunter x Hunter"),
    ("A lesson without pain is meaningless.", "Fullmetal Alchemist"),
    ("If you don't take risks, you can't create a future.", "One Piece"),
    ("I'm not stupid. I'm just too lazy to show how smart I am.", "OreGairu"),
    ("The world isn't perfect. But it's there for us.", "Fullmetal Alchemist"),
    ("I'll take a potato chip… and eat it.", "Death Note"),
    ("In this world, is the destiny of mankind controlled by something?", "Berserk"),
    ("A king without people is no king at all.", "Code Geass"),
    ("If you win, you live. If you lose, you die.", "Attack on Titan"),
    ("Fear is not evil. It tells you what your weakness is.", "Fairy Tail"),
    ("Power comes in response to a need, not a desire.", "Dragon Ball Z"),
    ("Hard work betrays none, but dreams betray many.", "OreGairu"),
    ("The only thing we're allowed to do is believe.", "Attack on Titan"),
    ("Whatever happens, happens.", "Cowboy Bebop"),
    ("You're gonna carry that weight.", "Cowboy Bebop"),
    ("It's not the face that makes someone a monster.", "Monster"),
    ("Wake up to reality. Nothing ever goes as planned.", "Naruto"),
    ("A person grows up when he's able to overcome hardships.", "Naruto"),
    ("Hell is other people.", "Jean-Paul Sartre"),
    ("Man is condemned to be free.", "Jean-Paul Sartre"),
    ("God is dead.", "Friedrich Nietzsche"),
    ("Whoever fights monsters should see to it that he does not become a monster.", "Nietzsche"),
    ("I think, therefore I am.", "René Descartes"),
    ("The unexamined life is not worth living.", "Socrates"),
    ("History is written by the victors.", "Winston Churchill"),
    ("In war, truth is the first casualty.", "Aeschylus"),
    ("I came, I saw, I conquered.", "Julius Caesar"),
    ("Never argue with stupid people, they will drag you down.", "Mark Twain"),
    ("Some people never go crazy. What truly horrible lives they must lead.", "Charles Bukowski"),
    ("If you're going through hell, keep going.", "Winston Churchill"),
    ("Facts do not cease to exist because they are ignored.", "Aldous Huxley"),
    ("If you're going to be stupid, you have to be tough.", "John Wayne"),
    ("The trouble with having an open mind is people will insist on coming along.", "Terry Pratchett"),
    ("It does not do to dwell on dreams and forget to live.", "Harry Potter"),
    ("Happiness can be found even in the darkest of times.", "Harry Potter"),
    ("We accept the love we think we deserve.", "The Perks of Being a Wallflower"),
    ("So it goes.", "Slaughterhouse-Five"),
    ("All we have to decide is what to do with the time that is given us.", "The Lord of the Rings"),
    ("Even the smallest person can change the course of the future.", "The Lord of the Rings"),
    ("It's a dangerous business going out your door.", "The Lord of the Rings"),
    ("Rip and tear, until it is done.", "DOOM"),
    ("Despite everything, it's still you.", "Undertale"),
    ("No cost too great.", "Hollow Knight"),
    ("The right man in the wrong place can make all the difference.", "Half-Life 2"),
    ("Rise and shine, Mr. Freeman.", "Half-Life 2"),
    ("War. War never changes.", "Fallout"),
    ("The cake is a lie.", "Portal"),
    ("Would you kindly?", "BioShock"),
    ("Nothing is true, everything is permitted.", "Assassin's Creed"),
    ("Prepare to die.", "Dark Souls"),
    ("Praise the Sun!", "Dark Souls"),
]

def load_config() -> Dict[str, Any]:
    """Load config from JSON with type hints."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except json.JSONDecodeError:
        logger.error("Config JSON corrupted, using defaults")
    except IOError as e:
        logger.error(f"Failed to read config: {e}")
    
    default: Dict[str, Any] = {
        "bot_token": os.getenv("BOT_TOKEN", "8736671676:AAHw92j_hH0nwbWaZpFG1cRIvPN-0MZbzm8"),
        "payment_token": os.getenv("PAYMENT_TOKEN", "https://t.me/tribute/app?startapp=dMvV"),
        "admin_ids": [int(x) for x in os.getenv("ADMIN_IDS", "6346043548").split(",") if x],
        "language": "en",
        "protect_content_default": False,
        "analytics_enabled": True,
        "version": "3.0.0",
        "log_channel": -1002202841137,
    }
    
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to write config: {e}")
    
    return default

CONFIG: Dict[str, Any] = load_config()

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def write_json(filepath: str, data: Dict[str, Any]) -> bool:
    """Atomic JSON write with error handling."""
    temp_file = filepath + '.tmp'
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        shutil.move(temp_file, filepath)
        return True
    except Exception as e:
        logger.error(f"Failed to write {filepath}: {e}")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass
        return False

def read_json(filepath: str) -> Dict[str, Any]:
    """Read JSON file safely with error handling."""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
    except json.JSONDecodeError:
        logger.error(f"Corrupted JSON: {filepath}")
        backup_path = filepath + '.corrupted'
        try:
            shutil.copy2(filepath, backup_path)
            logger.error(f"Backed up corrupted file to: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup corrupted file: {e}")
    except IOError as e:
        logger.error(f"IO Error reading {filepath}: {e}")
    
    return {}

def log_to_channel(bot: telebot.TeleBot, text: str, parse_mode: str = 'Markdown') -> None:
    """Send log message to log channel."""
    try:
        bot.send_message(LOG_CHANNEL_ID, text, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Failed to send log to channel: {e}")

# ============================================================================
# STATISTICS FUNCTIONS
# ============================================================================
def get_statistics() -> Dict[str, Any]:
    """Get bot statistics."""
    stats: Dict[str, Any] = read_json(STATISTICS_FILE)

    # If file empty or corrupted
    if not isinstance(stats, dict):
        stats = {}

    # sahi structure banane ki koshish mein.ballebaz
    stats.setdefault("total_users", 0)
    stats.setdefault("blocked_users", [])  # FIXED
    stats.setdefault("mau", {})            # FIXED
    stats.setdefault("daily_active", {})   # FIXED
    stats.setdefault("created_at", datetime.now().isoformat())
    stats.setdefault("payments", {
        "total_stars": 0,
        "total_donations": 0,
        "donors": []
    })

    # 🔥 umm i hope dis works
    if not isinstance(stats["mau"], dict):
        stats["mau"] = {}

    if not isinstance(stats["blocked_users"], list):
        stats["blocked_users"] = []

    if not isinstance(stats["daily_active"], dict):
        stats["daily_active"] = {}


    return stats

def update_statistics_mau(user_id: int) -> None:
    """Update MAU statistics safely."""
    try:
        stats: Dict[str, Any] = get_statistics()
        current_month = datetime.now().strftime("%Y-%m")
        current_day = datetime.now().strftime("%Y-%m-%d")

        # Ensure structure
        if current_month not in stats["mau"]:
            stats["mau"][current_month] = []

        if not isinstance(stats["mau"][current_month], list):
            stats["mau"][current_month] = []

        # Add user
        if user_id not in stats["mau"][current_month]:
            stats["mau"][current_month].append(user_id)

        # Daily active users
        stats["daily_active"][current_day] = len(set(stats["mau"][current_month]))

        write_json(STATISTICS_FILE, stats)

    except Exception as e:
        logger.error(f"Failed to update MAU statistics: {e}")

def get_mau_count() -> int:
    """Get current month's active users count safely."""
    try:
        stats: Dict[str, Any] = get_statistics()
        current_month = datetime.now().strftime("%Y-%m")

        mau = stats.get("mau", {})
        if not isinstance(mau, dict):
            return 0

        users = mau.get(current_month, [])
        if not isinstance(users, list):
            return 0

        return len(users)

    except Exception as e:
        logger.error(f"Failed to get MAU count: {e}")
        return 0

def update_blocked_user(user_id: int, blocked: bool = True) -> None:
    """Track blocked users."""
    try:
        stats: Dict[str, Any] = get_statistics()
        if "blocked_users" not in stats:
            stats["blocked_users"] = []
        
        if blocked and user_id not in stats["blocked_users"]:
            stats["blocked_users"].append(user_id)
        
        write_json(STATISTICS_FILE, stats)
    except Exception as e:
        logger.error(f"Failed to update blocked user: {e}")

def record_donation(user_id: int, amount_stars: int, user_name: str = "Unknown") -> None:
    """Record donation in statistics."""
    try:
        stats: Dict[str, Any] = get_statistics()
        
        if "payments" not in stats:
            stats["payments"] = {"total_stars": 0, "total_donations": 0, "donors": []}
        
        stats["payments"]["total_stars"] += amount_stars
        stats["payments"]["total_donations"] += 1
        
        donor_record = {
            "user_id": user_id,
            "name": user_name,
            "stars": amount_stars,
            "timestamp": datetime.now().isoformat()
        }
        
        stats["payments"]["donors"].append(donor_record)
        write_json(STATISTICS_FILE, stats)
    except Exception as e:
        logger.error(f"Failed to record donation: {e}")

# ============================================================================
# DONATE CONFIGURATION
# ============================================================================

def get_donate_config() -> Dict[str, Any]:
    """Get donate button configuration."""
    config: Dict[str, Any] = read_json(DONATE_CONFIG_FILE)
    if not config:
        config = {
            "enabled": True,
            "message": "❤️ Support our bot!\n\nYour donation helps us keep the bot running and add new features.",
            "buttons": [
                {"label": "🌟 Support ($1)", "stars": 1, "url": ""},
                {"label": "🌟🌟 Support ($5)", "stars": 5, "url": ""},
                {"label": "🌟🌟🌟 Support ($10)", "stars": 10, "url": ""},
                {"label": "🌟🌟🌟🌟 Support ($50)", "stars": 50, "url": ""}
            ],
            "custom_donation": {
                "enabled": True,
                "label": "✨ Custom Amount",
                "min_stars": 1,
                "max_stars": 50000
            },
            "external_buttons": [
                {"label": "☕ Buy Me Coffee", "url": ""},
                {"label": "💳 Other Methods", "url": ""}
            ],
            "button_layout": "side_by_side"
        }
        write_json(DONATE_CONFIG_FILE, config)
    return config

def update_donate_button(index: int, label: str, stars: int, url: str) -> Tuple[bool, str]:
    """Update donate button configuration."""
    try:
        if not (0 <= index < 4):
            return False, "Invalid button index (0-3)"
        
        config: Dict[str, Any] = get_donate_config()
        config["buttons"][index] = {
            "label": label,
            "stars": stars,
            "url": url
        }
        
        if write_json(DONATE_CONFIG_FILE, config):
            return True, f"Button {index + 1} updated"
        return False, "Failed to update button"
    except Exception as e:
        logger.error(f"Failed to update donate button: {e}")
        return False, str(e)

def update_custom_donation_config(enabled: bool, label: str, min_stars: int, max_stars: int) -> Tuple[bool, str]:
    """Update custom donation configuration."""
    try:
        config: Dict[str, Any] = get_donate_config()
        config["custom_donation"] = {
            "enabled": enabled,
            "label": label,
            "min_stars": min_stars,
            "max_stars": max_stars
        }
        
        if write_json(DONATE_CONFIG_FILE, config):
            return True, "Custom donation settings updated"
        return False, "Failed to update"
    except Exception as e:
        logger.error(f"Failed to update custom donation: {e}")
        return False, str(e)

def update_external_button(index: int, label: str, url: str) -> Tuple[bool, str]:
    """Update external payment button."""
    try:
        config: Dict[str, Any] = get_donate_config()
        if "external_buttons" not in config:
            config["external_buttons"] = []
        
        # Ensure we have enough slots
        while len(config["external_buttons"]) <= index:
            config["external_buttons"].append({"label": "", "url": ""})
        
        config["external_buttons"][index] = {"label": label, "url": url}
        
        if write_json(DONATE_CONFIG_FILE, config):
            return True, f"External button {index + 1} updated"
        return False, "Failed to update"
    except Exception as e:
        logger.error(f"Failed to update external button: {e}")
        return False, str(e)

# ============================================================================
# PAGE OPERATIONS
# ============================================================================

def get_all_pages() -> Dict[str, Any]:
    """Get all pages."""
    return read_json(CONTENT_FILE)

def get_page(page_id: str) -> Optional[Dict[str, Any]]:
    """Get single page by ID."""
    try:
        content: Dict[str, Any] = get_all_pages()
        return content.get(page_id, None)
    except Exception as e:
        logger.error(f"Failed to get page {page_id}: {e}")
        return None

def create_page(
    page_id: str,
    title: str,
    text: str,
    buttons: Optional[List[Dict[str, Any]]] = None,
    media: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    sections: Optional[List[Dict[str, Any]]] = None
) -> Tuple[bool, str]:
    """Create new page."""
    try:
        if not page_id or not title or not text:
            return False, "Missing required fields"
        
        content: Dict[str, Any] = get_all_pages()
        if page_id in content:
            return False, "Page already exists"
        
        content[page_id] = {
            "unique_id": page_id,
            "title": title,
            "text": text,
            "buttons": buttons or [],
            "media": media,
            "metadata": metadata or {
                "category": "docs",
                "lang": "en",
                "protected": False,
                "tags": [],
                "access": "public"
            },
            "sections": sections or []
        }
        
        if write_json(CONTENT_FILE, content):
            return True, "Page created"
        return False, "Failed to create page"
    except Exception as e:
        logger.error(f"Failed to create page {page_id}: {e}")
        return False, str(e)

def update_page(page_id: str, **kwargs: Any) -> Tuple[bool, str]:
    """Update page."""
    try:
        content: Dict[str, Any] = get_all_pages()
        if page_id not in content:
            return False, "Page not found"
        
        for key, value in kwargs.items():
            if key in content[page_id]:
                content[page_id][key] = value
        
        if write_json(CONTENT_FILE, content):
            return True, "Page updated"
        return False, "Failed to update page"
    except Exception as e:
        logger.error(f"Failed to update page {page_id}: {e}")
        return False, str(e)

def delete_page(page_id: str) -> Tuple[bool, str]:
    """Delete page."""
    try:
        if page_id == "home":
            return False, "Cannot delete home page"
        
        content: Dict[str, Any] = get_all_pages()
        if page_id not in content:
            return False, "Page not found"
        
        del content[page_id]
        
        if write_json(CONTENT_FILE, content):
            return True, "Page deleted"
        return False, "Failed to delete page"
    except Exception as e:
        logger.error(f"Failed to delete page {page_id}: {e}")
        return False, str(e)

def search_pages(keyword: str) -> List[Dict[str, Any]]:
    """Search pages by keyword."""
    try:
        if not keyword or len(keyword) > 100:
            return []
        
        content: Dict[str, Any] = get_all_pages()
        keyword_lower = keyword.lower()
        results: List[Dict[str, Any]] = []
        
        for page_id, page in content.items():
            if (keyword_lower in page.get("title", "").lower() or
                keyword_lower in page.get("text", "").lower()):
                results.append(page)
        
        return results
    except Exception as e:
        logger.error(f"Failed to search pages: {e}")
        return []

# ============================================================================
# VERSION CONTROL
# ============================================================================

def save_version(page_id: str, page_data: Dict[str, Any]) -> None:
    """Save page version."""
    try:
        versions: Dict[str, Any] = read_json(VERSIONS_FILE)
        if page_id not in versions:
            versions[page_id] = []
        
        version_entry = {
            "id": len(versions.get(page_id, [])),
            "data": page_data,
            "timestamp": datetime.now().isoformat()
        }
        
        versions[page_id].append(version_entry)
        write_json(VERSIONS_FILE, versions)
    except Exception as e:
        logger.error(f"Failed to save version for {page_id}: {e}")

def get_versions(page_id: str) -> List[Dict[str, Any]]:
    """Get page versions."""
    try:
        versions: Dict[str, Any] = read_json(VERSIONS_FILE)
        return versions.get(page_id, [])
    except Exception as e:
        logger.error(f"Failed to get versions for {page_id}: {e}")
        return []

def restore_version(page_id: str, version_id: int) -> Tuple[bool, str]:
    """Restore page to specific version."""
    try:
        versions: Dict[str, Any] = read_json(VERSIONS_FILE)
        if page_id not in versions or version_id >= len(versions[page_id]):
            return False, "Version not found"
        
        version_data = versions[page_id][version_id]
        if update_page(page_id, **version_data["data"]):
            return True, f"Restored to version {version_id}"
        return False, "Failed to restore version"
    except Exception as e:
        logger.error(f"Failed to restore version: {e}")
        return False, str(e)

# ============================================================================
# USER TRACKING
# ============================================================================

def migrate_users_data() -> None:
    """Migrate existing users to have all required fields."""
    try:
        users: Dict[str, Any] = read_json(USERS_FILE)
        migrated: int = 0
        
        for user_id_str, user_data in users.items():
            needs_migration = False
            
            if "pages_visited" not in user_data:
                user_data["pages_visited"] = [user_data.get("last_page", "home")]
                needs_migration = True
            if "buttons_clicked" not in user_data:
                user_data["buttons_clicked"] = []
                needs_migration = True
            if "xp" not in user_data:
                user_data["xp"] = 0
                needs_migration = True
            if "badges" not in user_data:
                user_data["badges"] = []
                needs_migration = True
            if "role" not in user_data:
                user_data["role"] = "user"
                needs_migration = True
            if "donated" not in user_data:
                user_data["donated"] = False
                needs_migration = True
            if "donation_amount" not in user_data:
                user_data["donation_amount"] = 0
                needs_migration = True
            
            if needs_migration:
                migrated += 1
        
        if migrated > 0:
            write_json(USERS_FILE, users)
            logger.info(f"✅ Migrated {migrated} users to new schema")
        else:
            logger.info("✅ All users already have required fields")
    except Exception as e:
        logger.error(f"Failed to migrate users: {e}")

def track_user(user_id: int, first_name: str, last_page: str = "home") -> None:
    """Track or update user."""
    try:
        users: Dict[str, Any] = read_json(USERS_FILE)
        user_id_str: str = str(user_id)
        
        if user_id_str not in users:
            users[user_id_str] = {
                "user_id": user_id,
                "first_name": first_name,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "visits": 1,
                "last_page": last_page,
                "pages_visited": [last_page],
                "buttons_clicked": [],
                "xp": 0,
                "badges": [],
                "role": "user",
                "donated": False,
                "donation_amount": 0
            }
        else:
            users[user_id_str]["last_seen"] = datetime.now().isoformat()
            users[user_id_str]["visits"] += 1
            users[user_id_str]["last_page"] = last_page
            
            if "pages_visited" not in users[user_id_str]:
                users[user_id_str]["pages_visited"] = [last_page]
            if "buttons_clicked" not in users[user_id_str]:
                users[user_id_str]["buttons_clicked"] = []
            if "xp" not in users[user_id_str]:
                users[user_id_str]["xp"] = 0
            if "badges" not in users[user_id_str]:
                users[user_id_str]["badges"] = []
            if "role" not in users[user_id_str]:
                users[user_id_str]["role"] = "user"
            if "donated" not in users[user_id_str]:
                users[user_id_str]["donated"] = False
            if "donation_amount" not in users[user_id_str]:
                users[user_id_str]["donation_amount"] = 0
            
            if last_page not in users[user_id_str]["pages_visited"]:
                users[user_id_str]["pages_visited"].append(last_page)
            
            users[user_id_str]["xp"] += 1
            update_badges(users[user_id_str])
        
        write_json(USERS_FILE, users)
        update_statistics_mau(user_id)
    except Exception as e:
        logger.error(f"Failed to track user {user_id}: {e}")

def track_button_click(user_id: int, button_label: str) -> None:
    """Track button clicks."""
    try:
        users: Dict[str, Any] = read_json(USERS_FILE)
        user_id_str: str = str(user_id)
        
        if user_id_str in users:
            if "buttons_clicked" not in users[user_id_str]:
                users[user_id_str]["buttons_clicked"] = []
            if "xp" not in users[user_id_str]:
                users[user_id_str]["xp"] = 0
            if "badges" not in users[user_id_str]:
                users[user_id_str]["badges"] = []
            
            users[user_id_str]["buttons_clicked"].append({
                "button": button_label,
                "timestamp": datetime.now().isoformat()
            })
            users[user_id_str]["xp"] += 2
            update_badges(users[user_id_str])
            write_json(USERS_FILE, users)
    except Exception as e:
        logger.error(f"Failed to track button click: {e}")

def update_badges(user_data: Dict[str, Any]) -> None:
    """Update user badges based on activity."""
    try:
        if not isinstance(user_data.get("badges"), list):
            user_data["badges"] = []
        
        badges: List[str] = user_data.get("badges", [])
        xp: int = user_data.get("xp", 0)
        visits: int = user_data.get("visits", 0)
        
        if xp >= 100 and "🔥 Active" not in badges:
            badges.append("🔥 Active")
        if visits >= 10 and "👑 Loyal" not in badges:
            badges.append("👑 Loyal")
        if user_data.get("donated", False) and "💎 Supporter" not in badges:
            badges.append("💎 Supporter")
        
        user_data["badges"] = badges
    except Exception as e:
        logger.error(f"Failed to update badges: {e}")

# ============================================================================
# BOOKMARKS
# ============================================================================

def add_bookmark(user_id: int, page_id: str) -> None:
    """Add page to bookmarks."""
    try:
        bookmarks: Dict[str, Any] = read_json(BOOKMARKS_FILE)
        user_id_str: str = str(user_id)
        
        if user_id_str not in bookmarks:
            bookmarks[user_id_str] = []
        
        if page_id not in bookmarks[user_id_str]:
            bookmarks[user_id_str].append(page_id)
            write_json(BOOKMARKS_FILE, bookmarks)
    except Exception as e:
        logger.error(f"Failed to add bookmark: {e}")

def remove_bookmark(user_id: int, page_id: str) -> None:
    """Remove page from bookmarks."""
    try:
        bookmarks: Dict[str, Any] = read_json(BOOKMARKS_FILE)
        user_id_str: str = str(user_id)
        
        if user_id_str in bookmarks and page_id in bookmarks[user_id_str]:
            bookmarks[user_id_str].remove(page_id)
            write_json(BOOKMARKS_FILE, bookmarks)
    except Exception as e:
        logger.error(f"Failed to remove bookmark: {e}")

def get_bookmarks(user_id: int) -> List[str]:
    """Get user bookmarks."""
    try:
        bookmarks: Dict[str, Any] = read_json(BOOKMARKS_FILE)
        return bookmarks.get(str(user_id), [])
    except Exception as e:
        logger.error(f"Failed to get bookmarks: {e}")
        return []

# ============================================================================
# FEEDBACK
# ============================================================================

def add_feedback(page_id: str, user_id: int, reaction: str) -> None:
    """Add feedback/reaction to page."""
    try:
        feedback: Dict[str, Any] = read_json(FEEDBACK_FILE)
        
        if page_id not in feedback:
            feedback[page_id] = []
        
        feedback[page_id].append({
            "user_id": user_id,
            "reaction": reaction,
            "timestamp": datetime.now().isoformat()
        })
        
        write_json(FEEDBACK_FILE, feedback)
    except Exception as e:
        logger.error(f"Failed to add feedback: {e}")

def get_feedback(page_id: str) -> List[Dict[str, Any]]:
    """Get page feedback."""
    try:
        feedback: Dict[str, Any] = read_json(FEEDBACK_FILE)
        return feedback.get(page_id, [])
    except Exception as e:
        logger.error(f"Failed to get feedback: {e}")
        return []

# ============================================================================
# BROADCAST
# ============================================================================

def add_broadcast_message(
    title: str,
    text: str,
    buttons: Optional[List[Dict[str, Any]]] = None,
    media: Optional[str] = None
) -> int:
    """Add broadcast message."""
    try:
        analytics: Dict[str, Any] = read_json(ANALYTICS_FILE)
        
        if "broadcasts" not in analytics:
            analytics["broadcasts"] = []
        
        broadcast_id: int = len(analytics.get("broadcasts", []))
        
        analytics["broadcasts"].append({
            "id": broadcast_id,
            "title": title,
            "text": text,
            "buttons": buttons or [],
            "media": media,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "sent_count": 0
        })
        
        write_json(ANALYTICS_FILE, analytics)
        return broadcast_id
    except Exception as e:
        logger.error(f"Failed to add broadcast: {e}")
        return -1

def send_broadcast(broadcast_id: int, bot: telebot.TeleBot) -> Tuple[bool, str]:
    """Send broadcast to all users."""
    try:
        analytics: Dict[str, Any] = read_json(ANALYTICS_FILE)
        broadcasts: List[Dict[str, Any]] = analytics.get("broadcasts", [])
        
        broadcast: Optional[Dict[str, Any]] = None
        for b in broadcasts:
            if b.get("id") == broadcast_id:
                broadcast = b
                break
        
        if not broadcast:
            return False, "Broadcast not found"
        
        users: Dict[str, Any] = read_json(USERS_FILE)
        sent_count: int = 0
        failed_count: int = 0
        
        for user_id_str in users.keys():
            try:
                user_id: int = int(user_id_str)
                markup = telebot.types.InlineKeyboardMarkup()
                
                for button in broadcast.get("buttons", []):
                    if button.get("type") == "url":
                        markup.add(telebot.types.InlineKeyboardButton(
                            button.get("label", "Link"),
                            url=button.get("url", "#")
                        ))
                
                bot.send_message(
                    user_id,
                    broadcast.get("text", ""),
                    parse_mode='Markdown',
                    reply_markup=markup if markup.keyboard else None
                )
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send broadcast to {user_id_str}: {e}")
                failed_count += 1
        
        broadcast["status"] = "sent"
        broadcast["sent_count"] = sent_count
        
        if write_json(ANALYTICS_FILE, analytics):
            log_to_channel(bot, f"📢 Broadcast sent to {sent_count} users (Failed: {failed_count})")
            return True, f"Sent to {sent_count}/{len(users)} users"
        
        return False, "Failed to update broadcast status"
    except Exception as e:
        logger.error(f"Failed to send broadcast: {e}")
        return False, str(e)

# ============================================================================
# ADMIN MANAGEMENT
# ============================================================================

def add_admin(user_id: int) -> Tuple[bool, str]:
    """Add user as admin."""
    try:
        if user_id in CONFIG["admin_ids"]:
            return False, "Already admin"
        
        CONFIG["admin_ids"].append(user_id)
        
        if write_json(CONFIG_FILE, CONFIG):
            return True, f"User {user_id} is now admin"
        return False, "Failed to update config"
    except Exception as e:
        logger.error(f"Failed to add admin: {e}")
        return False, str(e)

def remove_admin(user_id: int) -> Tuple[bool, str]:
    """Remove admin."""
    try:
        if user_id not in CONFIG["admin_ids"]:
            return False, "Not an admin"
        
        CONFIG["admin_ids"].remove(user_id)
        
        if write_json(CONFIG_FILE, CONFIG):
            return True, f"Admin {user_id} removed"
        return False, "Failed to update config"
    except Exception as e:
        logger.error(f"Failed to remove admin: {e}")
        return False, str(e)

def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in CONFIG.get("admin_ids", [])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_random_quote() -> Tuple[str, str]:
    """Get random quote."""
    try:
        return random.choice(QUOTES)
    except Exception as e:
        logger.error(f"Failed to get random quote: {e}")
        return ("No quote available", "Unknown")

def build_inline_keyboard(buttons: List[Tuple[str, str]]) -> telebot.types.InlineKeyboardMarkup:
    """Build inline keyboard from button list."""
    markup = telebot.types.InlineKeyboardMarkup()
    for label, callback in buttons:
        markup.add(telebot.types.InlineKeyboardButton(label, callback_data=callback))
    return markup

def send_message_safe(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    markup: Optional[telebot.types.InlineKeyboardMarkup] = None,
    parse_mode: str = 'Markdown'
) -> bool:
    """Send message with guaranteed formatting."""
    try:
        bot.send_message(
            chat_id,
            text,
            parse_mode=parse_mode,
            reply_markup=markup
        )
        return True
    except telebot.apihelper.ApiException as e:
        logger.error(f"Failed to send message: {e}")
        try:
            bot.send_message(chat_id, text)
        except Exception as e2:
            logger.error(f"Fallback send failed: {e2}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        return False

def format_page_content(page: Dict[str, Any], include_buttons: bool = False) -> str:
    """Format page content for display."""
    try:
        if not page:
            return "Page not found"
        
        text: str = f"*{page.get('title', 'Untitled')}*\n\n"
        text += page.get('text', '')
        
        if include_buttons and page.get('buttons'):
            text += "\n\n*Available actions:*\n"
            for i, btn in enumerate(page.get('buttons', []), 1):
                text += f"{i}. {btn.get('label', 'Action')}\n"
        
        return text
    except Exception as e:
        logger.error(f"Failed to format page content: {e}")
        return "Error formatting page"

def build_page_keyboard(page: Dict[str, Any]) -> telebot.types.InlineKeyboardMarkup:
    """Build keyboard for page."""
    markup = telebot.types.InlineKeyboardMarkup()
    
    try:
        for button in page.get("buttons", []):
            if button.get("type") == "page":
                markup.add(telebot.types.InlineKeyboardButton(
                    button.get("label", "Link"),
                    callback_data=f"page:{button.get('target', 'home')}"
                ))
            elif button.get("type") == "url":
                markup.add(telebot.types.InlineKeyboardButton(
                    button.get("label", "Link"),
                    url=button.get("url", "#")
                ))
    except Exception as e:
        logger.error(f"Failed to build page keyboard: {e}")
    
    return markup

def build_edit_menu_keyboard() -> telebot.types.InlineKeyboardMarkup:
    """Build admin edit menu keyboard."""
    return build_inline_keyboard([
        ("📝 Create Page", "edit:create"),
        ("✏️ Edit Page", "edit:select_edit"),
        ("🗑️ Delete Page", "edit:select_delete"),
        ("📊 Analytics", "edit:analytics"),
        ("💾 Backup", "edit:backup"),
        ("🎁 Donate Config", "edit:donate_config"),
        ("⭐ Donations", "edit:donations_stats"),
        ("❌ Close", "edit:close")
    ])

def build_page_list_keyboard(
    exclude: Optional[str] = None,
    prefix: str = ""
) -> telebot.types.InlineKeyboardMarkup:
    """Build keyboard with page list."""
    pages: Dict[str, Any] = get_all_pages()
    markup = telebot.types.InlineKeyboardMarkup()
    
    for page_id, page in list(pages.items())[:10]:
        if exclude and page_id == exclude:
            continue
        
        label: str = page.get('title', page_id)[:40]
        markup.add(telebot.types.InlineKeyboardButton(
            label,
            callback_data=f"{prefix}{page_id}"
        ))
    
    markup.add(telebot.types.InlineKeyboardButton("❌ Back", callback_data="edit:menu"))
    return markup

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

def initialize_bot() -> telebot.TeleBot:
    """Initialize bot with all handlers."""
    try:
        bot = telebot.TeleBot(CONFIG["bot_token"])
        bot.user_context = {}
        
        logger.info("Bot instance created")
        
        # Ensure files exist
        ensure_files()
        migrate_users_data()
        
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        raise
    
    # ===== START COMMAND =====
    @bot.message_handler(commands=['start'])
    def start(message: telebot.types.Message) -> None:
        """Start command - show home page."""
        try:
            user_id: int = message.from_user.id
            user_name: str = message.from_user.first_name or "User"
            
            track_user(user_id, user_name, "home")
            logger.info(f"User started: {user_id} - {user_name}")
            
            page: Optional[Dict[str, Any]] = get_page("home")
            if not page:
                send_message_safe(bot, user_id, "❌ Home page not found")
                return
            
            text: str = format_page_content(page)
            markup: telebot.types.InlineKeyboardMarkup = build_page_keyboard(page)
            
            if is_admin(user_id):
                markup.add(telebot.types.InlineKeyboardButton("⚙️ Admin Panel", callback_data="edit:menu"))
            
            markup.add(telebot.types.InlineKeyboardButton("🎁 Donate", callback_data="donate:menu"))
            
            send_message_safe(bot, user_id, text, markup)
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            send_message_safe(bot, message.from_user.id, "❌ Error loading home page")
    
    # ===== SEARCH COMMAND =====
    @bot.message_handler(commands=['search'])
    def search_cmd(message: telebot.types.Message) -> None:
        """Search pages."""
        try:
            user_id: int = message.from_user.id
            
            text = "*🔍 Search*\n\n"
            text += "Enter keyword to search pages:"
            
            msg = bot.send_message(user_id, text, parse_mode='Markdown')
            bot.register_next_step_handler(msg, handle_search)
        except Exception as e:
            logger.error(f"Error in search: {e}")
    
    def handle_search(message: telebot.types.Message) -> None:
        """Handle search input."""
        try:
            user_id: int = message.from_user.id
            keyword: str = message.text[:100] if message.text else ""
            
            results: List[Dict[str, Any]] = search_pages(keyword)
            
            if not results:
                send_message_safe(bot, user_id, "❌ No results found")
                return
            
            for page in results[:5]:
                text: str = format_page_content(page)
                markup: telebot.types.InlineKeyboardMarkup = build_page_keyboard(page)
                send_message_safe(bot, user_id, text, markup)
        except Exception as e:
            logger.error(f"Error handling search: {e}")
    
    # ===== PROFILE COMMAND =====
    @bot.message_handler(commands=['profile'])
    def profile_cmd(message: telebot.types.Message) -> None:
        """Show user profile."""
        try:
            user_id: int = message.from_user.id
            users: Dict[str, Any] = read_json(USERS_FILE)
            user: Optional[Dict[str, Any]] = users.get(str(user_id))
            
            if not user:
                send_message_safe(bot, user_id, "⚠️ Profile not found. Use /start first.")
                return
            
            text = "*👤 Your Profile*\n\n"
            text += f"*Name:* {user.get('first_name', 'Unknown')}\n"
            text += f"*Visits:* {user.get('visits', 0)}\n"
            text += f"*Pages Explored:* {len(user.get('pages_visited', []))}\n"
            text += f"*Actions:* {len(user.get('buttons_clicked', []))}\n"
            text += f"*XP:* ⭐ {user.get('xp', 0)}\n"
            
            badges: List[str] = user.get('badges', [])
            if badges:
                text += f"*Badges:* {' '.join(badges)}\n"
            
            if user.get('donated'):
                text += f"*Donated:* ❤️ {user.get('donation_amount', 0)} ⭐\n"
            
            markup = build_inline_keyboard([
                ("🏠 Home", "page:home"),
                ("🎁 Donate", "donate:menu")
            ])
            
            send_message_safe(bot, user_id, text, markup)
        except Exception as e:
            logger.error(f"Error in profile: {e}")
            send_message_safe(bot, message.from_user.id, "❌ Failed to load profile")
    
    # ===== BOOKMARKS COMMAND =====
    @bot.message_handler(commands=['bookmarks'])
    def bookmarks_cmd(message: telebot.types.Message) -> None:
        """Show bookmarks."""
        try:
            user_id: int = message.from_user.id
            bookmarks_list: List[str] = get_bookmarks(user_id)
            
            if not bookmarks_list:
                send_message_safe(bot, user_id, "📌 No bookmarks yet. Start exploring!")
                return
            
            text = "*📌 Your Bookmarks*\n\n"
            markup = telebot.types.InlineKeyboardMarkup()
            
            for page_id in bookmarks_list[:10]:
                page: Optional[Dict[str, Any]] = get_page(page_id)
                if page:
                    markup.add(telebot.types.InlineKeyboardButton(
                        page.get('title', page_id),
                        callback_data=f"page:{page_id}"
                    ))
            
            markup.add(telebot.types.InlineKeyboardButton("🏠 Home", callback_data="page:home"))
            send_message_safe(bot, user_id, text, markup)
        except Exception as e:
            logger.error(f"Error in bookmarks: {e}")
            send_message_safe(bot, message.from_user.id, "❌ Failed to load bookmarks")
    
    # ===== DONATE COMMAND =====
    @bot.message_handler(commands=['donate'])
    def donate_cmd(message: telebot.types.Message) -> None:
        """Donate command."""
        try:
            user_id: int = message.from_user.id
            show_donate_menu(message, user_id, bot)
        except Exception as e:
            logger.error(f"Error in donate command: {e}")
    
    def show_donate_menu(message: telebot.types.Message, user_id: int, bot: telebot.TeleBot) -> None:
        """Show donate menu with side-by-side buttons, custom amount, and external options."""
        try:
            config: Dict[str, Any] = get_donate_config()
            
            if not config.get("enabled"):
                send_message_safe(bot, user_id, "❌ Donations are currently disabled")
                return
            
            text = f"{config.get('message', '❤️ Support our bot!')}\n\n"
            markup = telebot.types.InlineKeyboardMarkup()
            
            # STAR BUTTONS - Side by side (2 per row)
            buttons = config.get("buttons", [])
            for i in range(0, len(buttons), 2):
                row = []
                for j in range(2):
                    if i + j < len(buttons):
                        btn = buttons[i + j]
                        row.append(telebot.types.InlineKeyboardButton(
                            btn.get("label", "Donate"),
                            callback_data=f"donate:button:{i + j}"
                        ))
                if row:
                    markup.add(*row)
            
            # CUSTOM AMOUNT BUTTON
            custom_config = config.get("custom_donation", {})
            if custom_config.get("enabled"):
                markup.add(telebot.types.InlineKeyboardButton(
                    custom_config.get("label", "✨ Custom Amount"),
                    callback_data="donate:custom"
                ))
            
            # EXTERNAL BUTTONS - Side by side (2 per row)
            external_buttons = config.get("external_buttons", [])
            for i in range(0, len(external_buttons), 2):
                row = []
                for j in range(2):
                    if i + j < len(external_buttons):
                        ext_btn = external_buttons[i + j]
                        if ext_btn.get("url"):  # Only show if URL is set
                            row.append(telebot.types.InlineKeyboardButton(
                                ext_btn.get("label", "Support"),
                                url=ext_btn.get("url")
                            ))
                if row:
                    markup.add(*row)
            
            markup.add(telebot.types.InlineKeyboardButton("🏠 Home", callback_data="page:home"))
            send_message_safe(bot, user_id, text, markup)
        except Exception as e:
            logger.error(f"Error showing donate menu: {e}")
    
    # ===== DONATE CALLBACK HANDLERS =====
    @bot.callback_query_handler(func=lambda call: call.data == "donate:menu")
    def donate_menu_callback(call: telebot.types.CallbackQuery) -> None:
        """Donate menu callback."""
        try:
            user_id: int = call.from_user.id
            show_donate_menu(call.message, user_id, bot)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in donate menu: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('donate:button:'))
    def donate_button_callback(call: telebot.types.CallbackQuery) -> None:
        """Handle donate button click."""
        try:
            user_id: int = call.from_user.id
            button_idx: int = int(call.data.split(':')[2])
            
            config: Dict[str, Any] = get_donate_config()
            button: Dict[str, Any] = config.get("buttons", [])[button_idx]
            
            stars: int = button.get("stars", 1)
            
            # Use Telegram Stars payment
            send_stars_invoice(bot, user_id, button_idx, button.get("label", "Donate"), stars)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in donate button: {e}")
            bot.answer_callback_query(call.id, "❌ Error processing donation", show_alert=True)
    
    # ===== CUSTOM DONATION HANDLER =====
    @bot.callback_query_handler(func=lambda call: call.data == "donate:custom")
    def custom_donation_callback(call: telebot.types.CallbackQuery) -> None:
        """Handle custom donation amount request."""
        try:
            user_id: int = call.from_user.id
            
            config: Dict[str, Any] = get_donate_config()
            custom_config: Dict[str, Any] = config.get("custom_donation", {})
            
            min_stars: int = custom_config.get("min_stars", 1)
            max_stars: int = custom_config.get("max_stars", 50000)
            
            text = f"*✨ Custom Donation*\n\n"
            text += f"Enter amount in stars:\n\n"
            text += f"*Minimum:* {min_stars} ⭐\n"
            text += f"*Maximum:* {max_stars} ⭐\n\n"
            text += "Example: `50` (to donate 50 stars)\n\n"
            text += "Or type `cancel` to go back"
            
            msg = bot.send_message(user_id, text, parse_mode='Markdown')
            bot.register_next_step_handler(msg, handle_custom_amount)
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            logger.error(f"Error in custom donation: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    def handle_custom_amount(message: telebot.types.Message) -> None:
        """Handle user's custom amount input."""
        try:
            user_id: int = message.from_user.id
            
            # Check if user wants to cancel
            if message.text.lower() == "cancel":
                send_message_safe(bot, user_id, "❌ Cancelled")
                return
            
            # Try to parse the amount
            try:
                stars: int = int(message.text)
            except ValueError:
                send_message_safe(bot, user_id, "❌ Please enter a valid number (e.g., `50`)")
                return
            
            # Get config limits
            config: Dict[str, Any] = get_donate_config()
            custom_config: Dict[str, Any] = config.get("custom_donation", {})
            
            min_stars: int = custom_config.get("min_stars", 1)
            max_stars: int = custom_config.get("max_stars", 50000)
            
            # Validate range
            if stars < min_stars:
                send_message_safe(bot, user_id, 
                    f"❌ Minimum donation is {min_stars} ⭐")
                return
            
            if stars > max_stars:
                send_message_safe(bot, user_id, 
                    f"❌ Maximum donation is {max_stars} ⭐")
                return
            
            if stars <= 0:
                send_message_safe(bot, user_id, 
                    f"❌ Amount must be greater than 0")
                return
            
            # Send confirmation message
            text = f"*Confirm Donation*\n\n"
            text += f"*Amount:* {stars} ⭐\n\n"
            text += "Click button below to proceed:"
            
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton(
                    f"✅ Confirm {stars} ⭐",
                    callback_data=f"donate:confirm_custom:{stars}"
                ),
                telebot.types.InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="donate:menu"
                )
            )
            
            send_message_safe(bot, user_id, text, markup)
            
        except Exception as e:
            logger.error(f"Error handling custom amount: {e}")
            send_message_safe(bot, user_id, f"❌ Error: {str(e)}")
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('donate:confirm_custom:'))
    def confirm_custom_donation(call: telebot.types.CallbackQuery) -> None:
        """Confirm and process custom donation amount."""
        try:
            user_id: int = call.from_user.id
            
            # Extract stars from callback data
            stars: int = int(call.data.split(':')[2])
            
            # Validate amount one more time
            config: Dict[str, Any] = get_donate_config()
            custom_config: Dict[str, Any] = config.get("custom_donation", {})
            
            max_stars: int = custom_config.get("max_stars", 50000)
            min_stars: int = custom_config.get("min_stars", 1)
            
            if stars < min_stars or stars > max_stars:
                bot.answer_callback_query(call.id, 
                    f"❌ Invalid amount ({min_stars}-{max_stars})", 
                    show_alert=True)
                return
            
            # Send invoice for custom amount
            send_custom_stars_invoice(bot, user_id, stars)
            bot.answer_callback_query(call.id)
            
        except ValueError:
            logger.error(f"Invalid stars value in confirm callback")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
        except Exception as e:
            logger.error(f"Error in confirm custom: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    def send_stars_invoice(
        bot: telebot.TeleBot,
        user_id: int,
        button_idx: int,
        title: str,
        stars: int
    ) -> None:
        """Send invoice for Telegram Stars payment."""
        try:
            prices: List[telebot.types.LabeledPrice] = [
                telebot.types.LabeledPrice(label=title, amount=stars)
            ]
            
            bot.send_invoice(
                user_id,
                title=title,
                description=f"Support us with {stars} stars",
                invoice_payload=f"donate_{button_idx}_{stars}",
                provider_token="",  # Empty for Telegram Stars
                currency="XTR",  # XTR is Telegram Stars currency
                prices=prices,
                start_parameter=f"donate_{button_idx}"
            )
        except Exception as e:
            logger.error(f"Failed to send invoice: {e}")
            send_message_safe(bot, user_id, f"❌ Error: {str(e)}")
    
    def send_custom_stars_invoice(
        bot: telebot.TeleBot,
        user_id: int,
        stars: int
    ) -> None:
        """Send invoice for custom Telegram Stars donation amount."""
        try:
            if stars < 1 or stars > 50000:
                send_message_safe(bot, user_id, "❌ Invalid donation amount")
                return
            
            prices: List[telebot.types.LabeledPrice] = [
                telebot.types.LabeledPrice(label=f"Custom Donation ({stars} ⭐)", amount=stars)
            ]
            
            bot.send_invoice(
                user_id,
                title=f"Custom Donation - {stars} Stars",
                description=f"Support us with {stars} ⭐",
                invoice_payload=f"donate_custom_{stars}",
                provider_token="",  # Empty for Telegram Stars
                currency="XTR",  # Telegram Stars currency
                prices=prices,
                start_parameter=f"donate_custom_{stars}"
            )
            
            logger.info(f"Custom invoice sent to user {user_id}: {stars} stars")
            
        except Exception as e:
            logger.error(f"Failed to send custom invoice: {e}")
            send_message_safe(bot, user_id, f"❌ Error: {str(e)}")
    
    
    # ===== PRE-CHECKOUT QUERY HANDLER =====
    @bot.pre_checkout_query_handler(func=lambda query: True)
    def process_pre_checkout_query(query: telebot.types.PreCheckoutQuery) -> None:
        """Process pre-checkout query."""
        try:
            bot.answer_pre_checkout_query(query.id, ok=True)
        except Exception as e:
            logger.error(f"Error in pre-checkout: {e}")
            bot.answer_pre_checkout_query(query.id, ok=False, error_message="Payment failed")
    
    # ===== SUCCESSFUL PAYMENT HANDLER =====
    @bot.message_handler(content_types=['successful_payment'])
    def process_successful_payment(message: telebot.types.Message) -> None:
        """Handle successful payment."""
        try:
            user_id: int = message.from_user.id
            user_name: str = message.from_user.first_name or "User"
            payment: telebot.types.SuccessfulPayment = message.successful_payment
            
            # Parse stars and button index from invoice payload
            payload_parts: List[str] = payment.invoice_payload.split('_')
            stars: int = int(payload_parts[-1])
            
            # Update user donation info
            users: Dict[str, Any] = read_json(USERS_FILE)
            user_id_str: str = str(user_id)
            
            if user_id_str in users:
                users[user_id_str]["donated"] = True
                users[user_id_str]["donation_amount"] = users[user_id_str].get("donation_amount", 0) + stars
                update_badges(users[user_id_str])
                write_json(USERS_FILE, users)
            
            # Record donation in statistics
            record_donation(user_id, stars, user_name)
            
            # Send thank you message
            text = f"🎉 Thank you for donating {stars} ⭐!\n\n"
            text += "Your support helps us keep the bot running and add new features.\n"
            text += "You have been added to our supporters list! 💎"
            
            markup = build_inline_keyboard([
                ("🏠 Home", "page:home")
            ])
            
            send_message_safe(bot, user_id, text, markup)
            
            # Log to channel
            log_to_channel(
                bot,
                f"💖 New donation!\n"
                f"User: {user_name} ({user_id})\n"
                f"Amount: {stars} ⭐"
            )
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            send_message_safe(bot, message.from_user.id, "❌ Error processing payment")
    
    # ===== HELP COMMAND =====
    @bot.message_handler(commands=['help'])
    def help_cmd(message: telebot.types.Message) -> None:
        """Help command with random quote."""
        try:
            user_id: int = message.from_user.id
            quote, author = get_random_quote()
            
            text = "*📚 Help & Information*\n\n"
            text += "*Available Commands:*\n"
            text += "/start - 📖 Go to home\n"
            text += "/search - 🔍 Search pages\n"
            text += "/profile - 👤 Your profile\n"
            text += "/bookmarks - 📌 Bookmarks\n"
            text += "/donate - 🎁 Support us\n"
            text += "/help - ❓ This help\n"
            
            if is_admin(user_id):
                text += "\n*Admin Commands:*\n"
                text += "/edit - ⚙️ Edit pages\n"
                text += "/addadmin - 👮 Add admin\n"
                text += "/broadcast - 📢 Send broadcast\n"
                text += "/stats - 📊 Statistics\n"
            
            text += f"\n*💡 Random Quote:*\n\n"
            text += f"_{quote}_\n"
            text += f"— {author}"
            
            markup = build_inline_keyboard([
                ("🏠 Home", "page:home"),
                ("🎁 Donate", "donate:menu")
            ])
            
            send_message_safe(bot, user_id, text, markup)
        except Exception as e:
            logger.error(f"Error in help: {e}")
            send_message_safe(bot, message.from_user.id, "❌ Failed to load help")
    
    # ===== ADMIN EDIT COMMAND =====
    @bot.message_handler(commands=['edit'])
    def edit_cmd(message: telebot.types.Message) -> None:
        """Admin edit command."""
        try:
            user_id: int = message.from_user.id
            
            if not is_admin(user_id):
                send_message_safe(bot, user_id, "❌ Admin only")
                return
            
            text = "*⚙️ Admin Panel*\n\n"
            text += "Select an action:"
            
            markup = build_edit_menu_keyboard()
            send_message_safe(bot, user_id, text, markup)
        except Exception as e:
            logger.error(f"Error in edit command: {e}")
            send_message_safe(bot, message.from_user.id, "❌ Error loading admin panel")
    
    # ===== STATISTICS COMMAND =====
    @bot.message_handler(commands=['stats'])
    def stats_cmd(message: telebot.types.Message) -> None:
        """Show statistics."""
        try:
            user_id: int = message.from_user.id
            
            if not is_admin(user_id):
                send_message_safe(bot, user_id, "❌ Admin only")
                return
            
            pages: Dict[str, Any] = get_all_pages()
            users: Dict[str, Any] = read_json(USERS_FILE)
            stats: Dict[str, Any] = get_statistics()
            
            mau: int = get_mau_count()
            blocked: int = len(stats.get("blocked_users", []))
            total_stars: int = stats.get("payments", {}).get("total_stars", 0)
            donations: int = stats.get("payments", {}).get("total_donations", 0)
            
            text = "*📊 Bot Statistics*\n\n"
            text += f"*Pages:* {len(pages)}\n"
            text += f"*Total Users:* {len(users)}\n"
            text += f"*Monthly Active Users:* {mau}\n"
            text += f"*Blocked Users:* {blocked}\n"
            text += f"\n*Donations:*\n"
            text += f"*Total Stars Received:* {total_stars} ⭐\n"
            text += f"*Total Donations:* {donations}\n"
            
            if donations > 0:
                text += f"*Avg per donation:* {total_stars // donations} ⭐\n"
            
            markup = build_edit_menu_keyboard()
            send_message_safe(bot, user_id, text, markup)
        except Exception as e:
            logger.error(f"Error in stats: {e}")
            send_message_safe(bot, message.from_user.id, "❌ Failed to load statistics")
    
    # ===== ADMIN PAGE CALLBACKS =====
    @bot.callback_query_handler(func=lambda call: call.data == "edit:menu")
    def edit_menu(call: telebot.types.CallbackQuery) -> None:
        """Edit menu callback."""
        try:
            user_id: int = call.from_user.id
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
                return
            
            text = "*⚙️ Admin Panel*\n\nSelect an action:"
            markup = build_edit_menu_keyboard()
            
            bot.edit_message_text(text, user_id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in edit menu: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data == "edit:close")
    def edit_close(call: telebot.types.CallbackQuery) -> None:
        """Close edit menu."""
        try:
            bot.edit_message_text("✅ Closed", call.from_user.id, call.message.message_id)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error closing menu: {e}")
    
    # ===== DONATE CONFIG ADMIN =====
    @bot.callback_query_handler(func=lambda call: call.data == "edit:donate_config")
    def donate_config_menu(call: telebot.types.CallbackQuery) -> None:
        """Donate configuration menu."""
        try:
            user_id: int = call.from_user.id
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
                return
            
            config: Dict[str, Any] = get_donate_config()
            
            text = "*🎁 Donate Configuration*\n\n"
            text += "*Star Buttons:*\n"
            
            for idx, btn in enumerate(config.get("buttons", []), 1):
                text += f"{idx}. {btn.get('label')} - {btn.get('stars')} ⭐\n"
            
            custom_config = config.get("custom_donation", {})
            text += f"\n*Custom Amount:* {'✅ Enabled' if custom_config.get('enabled') else '❌ Disabled'}\n"
            text += f"  Range: {custom_config.get('min_stars', 1)} - {custom_config.get('max_stars', 50000)} ⭐\n"
            
            external_buttons = config.get("external_buttons", [])
            text += f"\n*External Payment Methods:*\n"
            for idx, btn in enumerate(external_buttons, 1):
                url_status = "✅" if btn.get("url") else "❌"
                text += f"{idx}. {btn.get('label')} {url_status}\n"
            
            markup = telebot.types.InlineKeyboardMarkup()
            
            # Star buttons
            for idx in range(4):
                markup.add(telebot.types.InlineKeyboardButton(
                    f"Edit Button {idx + 1}",
                    callback_data=f"donate_config:edit:{idx}"
                ))
            
            # Custom donation
            markup.add(telebot.types.InlineKeyboardButton(
                "⚙️ Custom Amount Settings",
                callback_data="donate_config:custom"
            ))
            
            # External buttons
            for idx in range(len(external_buttons)):
                markup.add(telebot.types.InlineKeyboardButton(
                    f"Edit {external_buttons[idx].get('label')}",
                    callback_data=f"donate_config:external:{idx}"
                ))
            
            markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="edit:menu"))
            
            send_message_safe(bot, user_id, text, markup)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in donate config: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data == "donate_config:custom")
    def custom_donation_settings(call: telebot.types.CallbackQuery) -> None:
        """Edit custom donation settings."""
        try:
            user_id: int = call.from_user.id
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
                return
            
            config: Dict[str, Any] = get_donate_config()
            custom_config = config.get("custom_donation", {})
            
            text = "*⚙️ Custom Donation Settings*\n\n"
            text += f"*Status:* {'Enabled' if custom_config.get('enabled') else 'Disabled'}\n"
            text += f"*Label:* {custom_config.get('label', '✨ Custom Amount')}\n"
            text += f"*Min:* {custom_config.get('min_stars', 1)} ⭐\n"
            text += f"*Max:* {custom_config.get('max_stars', 50000)} ⭐\n\n"
            text += "Send format to update:\n"
            text += "`enabled | label | min | max`\n\n"
            text += "Example:\n"
            text += "`true | ✨ Custom Donation | 1 | 50000`\n\n"
            text += "Or type 'skip' to cancel"
            
            msg = bot.send_message(user_id, text, parse_mode='Markdown')
            
            def handle_custom_settings(m: telebot.types.Message) -> None:
                """Handle custom settings edit."""
                try:
                    if m.text.lower() == "skip":
                        send_message_safe(bot, user_id, "✅ Skipped")
                        return
                    
                    parts: List[str] = m.text.split('|')
                    if len(parts) < 4:
                        send_message_safe(bot, user_id, "❌ Invalid format. Expected: enabled | label | min | max")
                        return
                    
                    enabled: bool = parts[0].strip().lower() == 'true'
                    label: str = parts[1].strip()
                    min_stars: int = int(parts[2].strip())
                    max_stars: int = int(parts[3].strip())
                    
                    if min_stars <= 0 or max_stars <= 0 or min_stars > max_stars:
                        send_message_safe(bot, user_id, "❌ Invalid stars range")
                        return
                    
                    success, msg_text = update_custom_donation_config(enabled, label, min_stars, max_stars)
                    
                    if success:
                        send_message_safe(bot, user_id, f"✅ {msg_text}")
                        log_to_channel(bot, f"🎁 Custom donation settings updated by admin {user_id}")
                    else:
                        send_message_safe(bot, user_id, f"❌ {msg_text}")
                except ValueError:
                    send_message_safe(bot, user_id, "❌ Invalid number format")
                except Exception as e:
                    logger.error(f"Error handling custom settings: {e}")
                    send_message_safe(bot, user_id, f"❌ Error: {str(e)}")
            
            bot.register_next_step_handler(msg, handle_custom_settings)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in custom settings: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('donate_config:external:'))
    def external_button_edit(call: telebot.types.CallbackQuery) -> None:
        """Edit external payment button."""
        try:
            user_id: int = call.from_user.id
            button_idx: int = int(call.data.split(':')[2])
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
                return
            
            config: Dict[str, Any] = get_donate_config()
            external_buttons = config.get("external_buttons", [])
            
            if button_idx >= len(external_buttons):
                bot.answer_callback_query(call.id, "❌ Button not found", show_alert=True)
                return
            
            button = external_buttons[button_idx]
            
            text = f"*Edit External Button {button_idx + 1}*\n\n"
            text += f"Current: {button.get('label')}\n"
            text += f"URL: {button.get('url') or 'Not set'}\n\n"
            text += "Send new button info in format:\n"
            text += "`Label | URL`\n\n"
            text += "Example:\n"
            text += "`☕ Buy Me Coffee | https://buymeacoffee.com/yourname`\n\n"
            text += "Or type 'skip' to keep current\n"
            text += "Or type 'clear' to remove the button"
            
            msg = bot.send_message(user_id, text, parse_mode='Markdown')
            
            def handle_external_edit(m: telebot.types.Message) -> None:
                """Handle external button edit."""
                try:
                    if m.text.lower() == "skip":
                        send_message_safe(bot, user_id, "✅ Skipped")
                        return
                    
                    if m.text.lower() == "clear":
                        success, msg_text = update_external_button(button_idx, "", "")
                        if success:
                            send_message_safe(bot, user_id, f"✅ Button cleared")
                            log_to_channel(bot, f"🎁 External button {button_idx + 1} cleared by admin {user_id}")
                        else:
                            send_message_safe(bot, user_id, f"❌ {msg_text}")
                        return
                    
                    parts: List[str] = m.text.split('|')
                    if len(parts) < 2:
                        send_message_safe(bot, user_id, "❌ Invalid format. Expected: Label | URL")
                        return
                    
                    label: str = parts[0].strip()
                    url: str = parts[1].strip()
                    
                    if not url.startswith(('http://', 'https://')):
                        send_message_safe(bot, user_id, "❌ URL must start with http:// or https://")
                        return
                    
                    success, msg_text = update_external_button(button_idx, label, url)
                    
                    if success:
                        send_message_safe(bot, user_id, f"✅ {msg_text}")
                        log_to_channel(bot, f"🎁 External button {button_idx + 1} ({label}) updated by admin {user_id}")
                    else:
                        send_message_safe(bot, user_id, f"❌ {msg_text}")
                except Exception as e:
                    logger.error(f"Error handling external edit: {e}")
                    send_message_safe(bot, user_id, f"❌ Error: {str(e)}")
            
            bot.register_next_step_handler(msg, handle_external_edit)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in external button edit: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('donate_config:edit:'))
    def donate_config_edit(call: telebot.types.CallbackQuery) -> None:
        """Edit donate button."""
        try:
            user_id: int = call.from_user.id
            button_idx: int = int(call.data.split(':')[2])
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
                return
            
            config: Dict[str, Any] = get_donate_config()
            button: Dict[str, Any] = config.get("buttons", [])[button_idx]
            
            text = f"*Edit Button {button_idx + 1}*\n\n"
            text += f"Current: {button.get('label')} - {button.get('stars')} ⭐\n\n"
            text += "Send new button info in format:\n"
            text += "`Label | Stars | URL`\n\n"
            text += "Example:\n"
            text += "`🌟 Support ($5) | 5 | https://example.com`\n\n"
            text += "Or just press 'Skip' to keep current"
            
            msg = bot.send_message(user_id, text, parse_mode='Markdown')
            
            def handle_button_edit(m: telebot.types.Message) -> None:
                """Handle button edit input."""
                try:
                    if m.text.lower() == "skip":
                        send_message_safe(bot, user_id, "✅ Skipped")
                        return
                    
                    parts: List[str] = m.text.split('|')
                    if len(parts) < 2:
                        send_message_safe(bot, user_id, "❌ Invalid format")
                        return
                    
                    label: str = parts[0].strip()
                    stars: int = int(parts[1].strip())
                    url: str = parts[2].strip() if len(parts) > 2 else ""
                    
                    success, msg_text = update_donate_button(button_idx, label, stars, url)
                    
                    if success:
                        send_message_safe(bot, user_id, f"✅ {msg_text}")
                        log_to_channel(bot, f"🎁 Donate button {button_idx + 1} updated by admin {user_id}")
                    else:
                        send_message_safe(bot, user_id, f"❌ {msg_text}")
                except ValueError:
                    send_message_safe(bot, user_id, "❌ Invalid stars number")
                except Exception as e:
                    logger.error(f"Error handling button edit: {e}")
                    send_message_safe(bot, user_id, f"❌ Error: {str(e)}")
            
            bot.register_next_step_handler(msg, handle_button_edit)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in donate config edit: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    # ===== DONATION STATS FOR ADMIN =====
    @bot.callback_query_handler(func=lambda call: call.data == "edit:donations_stats")
    def donations_stats(call: telebot.types.CallbackQuery) -> None:
        """Show donation statistics."""
        try:
            user_id: int = call.from_user.id
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
                return
            
            stats: Dict[str, Any] = get_statistics()
            payments: Dict[str, Any] = stats.get("payments", {})
            donors: List[Dict[str, Any]] = payments.get("donors", [])
            
            text = "*💎 Donation Statistics*\n\n"
            text += f"*Total Stars:* {payments.get('total_stars', 0)} ⭐\n"
            text += f"*Total Donations:* {payments.get('total_donations', 0)}\n"
            
            if donors:
                text += f"\n*Recent Donors:*\n"
                for donor in donors[-5:]:
                    text += f"• {donor.get('name')} - {donor.get('stars')} ⭐\n"
            
            markup = build_edit_menu_keyboard()
            send_message_safe(bot, user_id, text, markup)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in donations stats: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    # ===== PAGE NAVIGATION CALLBACK =====
    @bot.callback_query_handler(func=lambda call: call.data.startswith('page:'))
    def page_callback(call: telebot.types.CallbackQuery) -> None:
        """Handle page navigation."""
        try:
            user_id: int = call.from_user.id
            page_id: str = call.data.split(':')[1]
            
            page: Optional[Dict[str, Any]] = get_page(page_id)
            if not page:
                bot.answer_callback_query(call.id, "❌ Page not found", show_alert=True)
                return
            
            track_user(user_id, call.from_user.first_name or "User", page_id)
            
            text: str = format_page_content(page)
            markup: telebot.types.InlineKeyboardMarkup = build_page_keyboard(page)
            
            # Add default buttons
            btn_row = []
            btn_row.append(telebot.types.InlineKeyboardButton("❤️ Bookmark", callback_data=f"bookmark:add:{page_id}"))
            markup.add(*btn_row)
            
            if is_admin(user_id):
                markup.add(telebot.types.InlineKeyboardButton("✏️ Edit", callback_data=f"edit_page:{page_id}"))
            
            markup.add(telebot.types.InlineKeyboardButton("🏠 Home", callback_data="page:home"))
            
            send_message_safe(bot, user_id, text, markup)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in page callback: {e}")
            bot.answer_callback_query(call.id, "❌ Error loading page", show_alert=True)
    
    # ===== BOOKMARK CALLBACKS =====
    @bot.callback_query_handler(func=lambda call: call.data.startswith('bookmark:'))
    def bookmark_callback(call: telebot.types.CallbackQuery) -> None:
        """Handle bookmark actions."""
        try:
            user_id: int = call.from_user.id
            action: str = call.data.split(':')[1]
            page_id: str = call.data.split(':')[2]
            
            if action == "add":
                add_bookmark(user_id, page_id)
                bot.answer_callback_query(call.id, "📌 Bookmarked!")
            elif action == "remove":
                remove_bookmark(user_id, page_id)
                bot.answer_callback_query(call.id, "📌 Bookmark removed")
        except Exception as e:
            logger.error(f"Error in bookmark callback: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    # ===== FEEDBACK CALLBACKS =====
    # ===== BROADCAST COMMAND =====
    @bot.message_handler(commands=['broadcast'])
    def broadcast_cmd(message: telebot.types.Message) -> None:
        """Admin broadcast command - improved."""
        try:
            user_id: int = message.from_user.id
            
            if not is_admin(user_id):
                send_message_safe(bot, user_id, "❌ Admin only")
                return
            
            text = "*📢 Create Broadcast*\n\n"
            text += "Send the message you want to broadcast:\n"
            text += "• Text only\n"
            text += "• Or reply to a message with content\n"
            text += "• Max 4000 characters"
            
            msg = bot.send_message(user_id, text, parse_mode='Markdown')
            bot.register_next_step_handler(msg, handle_broadcast_input)
        except Exception as e:
            logger.error(f"Error in broadcast: {e}")
            send_message_safe(bot, message.from_user.id, "❌ Error starting broadcast")
    
    def handle_broadcast_input(message: telebot.types.Message) -> None:
        """Handle broadcast message input."""
        try:
            user_id: int = message.from_user.id
            content: str = message.text or "Message"
            
            if len(content) > 4000:
                send_message_safe(bot, user_id, "❌ Message too long (max 4000 chars)")
                return
            
            broadcast_id: int = add_broadcast_message(
                title="Broadcast",
                text=content,
                buttons=[],
                media=None
            )
            
            if broadcast_id < 0:
                send_message_safe(bot, user_id, "❌ Failed to create broadcast")
                return
            
            text = "*📢 Broadcast Preview*\n\n"
            text += f"{content}\n\n"
            text += "Send to all users?"
            
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton("✅ Send Now", callback_data=f"broadcast:confirm:{broadcast_id}"),
                telebot.types.InlineKeyboardButton("❌ Cancel", callback_data="edit:menu")
            )
            
            send_message_safe(bot, user_id, text, markup)
        except Exception as e:
            logger.error(f"Error handling broadcast input: {e}")
            send_message_safe(bot, message.from_user.id, f"❌ Error: {str(e)}")
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('broadcast:confirm:'))
    def confirm_broadcast(call: telebot.types.CallbackQuery) -> None:
        """Confirm and send broadcast."""
        try:
            user_id: int = call.from_user.id
            broadcast_id: int = int(call.data.split(':')[2])
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
                return
            
            success, msg_text = send_broadcast(broadcast_id, bot)
            
            if success:
                send_message_safe(bot, user_id, f"✅ {msg_text}")
                logger.info(f"Broadcast {broadcast_id} sent by admin {user_id}")
            else:
                send_message_safe(bot, user_id, f"❌ {msg_text}")
            
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error confirming broadcast: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    # ===== PAGE EDITING CALLBACKS =====
    @bot.callback_query_handler(func=lambda call: call.data == "edit:create")
    def create_page_start(call: telebot.types.CallbackQuery) -> None:
        """Start page creation."""
        try:
            user_id: int = call.from_user.id
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
                return
            
            text = "*📝 Create Page*\n\n"
            text += "Send page info in format:\n"
            text += "`page_id | Title | Content`\n\n"
            text += "Example:\n"
            text += "`about | About Us | This is about our project`"
            
            msg = bot.send_message(user_id, text, parse_mode='Markdown')
            bot.register_next_step_handler(msg, handle_page_creation)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in create page: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    def handle_page_creation(message: telebot.types.Message) -> None:
        """Handle page creation input."""
        try:
            user_id: int = message.from_user.id
            
            parts: List[str] = message.text.split('|') if message.text else []
            if len(parts) < 3:
                send_message_safe(bot, user_id, "❌ Invalid format")
                return
            
            page_id: str = parts[0].strip()
            title: str = parts[1].strip()
            content: str = parts[2].strip()
            
            success, msg_text = create_page(page_id, title, content)
            
            if success:
                send_message_safe(bot, user_id, f"✅ {msg_text}")
                log_to_channel(bot, f"📄 New page created: {page_id}")
            else:
                send_message_safe(bot, user_id, f"❌ {msg_text}")
        except Exception as e:
            logger.error(f"Error creating page: {e}")
            send_message_safe(bot, message.from_user.id, f"❌ Error: {str(e)}")
    
    @bot.callback_query_handler(func=lambda call: call.data == "edit:select_edit")
    def edit_select(call: telebot.types.CallbackQuery) -> None:
        """Select page to edit."""
        try:
            user_id: int = call.from_user.id
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
                return
            
            text = "*✏️ Select Page to Edit*"
            markup = build_page_list_keyboard(prefix="edit_select:")
            
            send_message_safe(bot, user_id, text, markup)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in edit select: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('edit_select:'))
    def edit_select_page(call: telebot.types.CallbackQuery) -> None:
        """Start editing selected page."""
        try:
            user_id: int = call.from_user.id
            page_id: str = call.data.split(':', 1)[1]
            
            page: Optional[Dict[str, Any]] = get_page(page_id)
            if not page:
                bot.answer_callback_query(call.id, "Page not found", show_alert=True)
                return
            
            text = f"*✏️ Editing: {page.get('title', page_id)}*\n\n"
            text += "Send new content in format:\n"
            text += "`Title | Content`\n\n"
            text += "Or send just the content to keep title"
            
            msg = bot.send_message(user_id, text, parse_mode='Markdown')
            
            def handle_page_edit(m: telebot.types.Message) -> None:
                """Handle page edit input."""
                try:
                    if not m.text:
                        send_message_safe(bot, user_id, "❌ Invalid input")
                        return
                    
                    if '|' in m.text:
                        parts: List[str] = m.text.split('|')
                        title: str = parts[0].strip()
                        content: str = parts[1].strip()
                    else:
                        title: str = page.get('title')
                        content: str = m.text
                    
                    success, msg_text = update_page(page_id, title=title, text=content)
                    
                    if success:
                        send_message_safe(bot, user_id, f"✅ {msg_text}")
                        save_version(page_id, page)
                        log_to_channel(bot, f"✏️ Page {page_id} updated by admin {user_id}")
                    else:
                        send_message_safe(bot, user_id, f"❌ {msg_text}")
                except Exception as e:
                    logger.error(f"Error editing page: {e}")
                    send_message_safe(bot, user_id, f"❌ Error: {str(e)}")
            
            bot.register_next_step_handler(msg, handle_page_edit)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error selecting page to edit: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data == "edit:select_delete")
    def delete_select(call: telebot.types.CallbackQuery) -> None:
        """Select page to delete."""
        try:
            user_id: int = call.from_user.id
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
                return
            
            text = "*🗑️ Select Page to Delete*"
            markup = build_page_list_keyboard(exclude='home', prefix="delete_select:")
            
            send_message_safe(bot, user_id, text, markup)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in delete select: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_select:'))
    def delete_page_confirm(call: telebot.types.CallbackQuery) -> None:
        """Confirm page deletion."""
        try:
            user_id: int = call.from_user.id
            page_id: str = call.data.split(':', 1)[1]
            
            page: Optional[Dict[str, Any]] = get_page(page_id)
            if not page:
                bot.answer_callback_query(call.id, "Not found", show_alert=True)
                return
            
            text = f"⚠️ Delete *{page.get('title', page_id)}*?\n\nThis cannot be undone."
            
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_final:{page_id}"),
                telebot.types.InlineKeyboardButton("❌ Cancel", callback_data="edit:menu")
            )
            
            send_message_safe(bot, user_id, text, markup)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in delete confirm: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_final:'))
    def delete_page_final(call: telebot.types.CallbackQuery) -> None:
        """Delete page."""
        try:
            user_id: int = call.from_user.id
            page_id: str = call.data.split(':', 1)[1]
            
            success, msg_text = delete_page(page_id)
            bot.answer_callback_query(call.id, msg_text, show_alert=True)
            
            if success:
                send_message_safe(bot, user_id, "✅ Deleted!")
                log_to_channel(bot, f"🗑️ Page {page_id} deleted by admin {user_id}")
        except Exception as e:
            logger.error(f"Error deleting page: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data == "edit:analytics")
    def show_analytics(call: telebot.types.CallbackQuery) -> None:
        """Show analytics."""
        try:
            user_id: int = call.from_user.id
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
                return
            
            pages: Dict[str, Any] = get_all_pages()
            users: Dict[str, Any] = read_json(USERS_FILE)
            
            text = "*📊 Analytics*\n\n"
            text += f"*Pages:* {len(pages)}\n"
            text += f"*Users:* {len(users)}\n"
            text += f"*Total XP:* {sum(u.get('xp', 0) for u in users.values())}\n"
            
            markup = build_edit_menu_keyboard()
            send_message_safe(bot, user_id, text, markup)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in analytics: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data == "edit:backup")
    def create_backup(call: telebot.types.CallbackQuery) -> None:
        """Create backup."""
        try:
            user_id: int = call.from_user.id
            
            timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file: str = os.path.join(DATA_DIR, 'backups', f'content_{timestamp}.json')
            content: Dict[str, Any] = get_all_pages()
            
            if write_json(backup_file, content):
                send_message_safe(bot, user_id, f"✅ Backup created: content_{timestamp}.json")
                log_to_channel(bot, f"💾 Backup created by admin {user_id}")
            else:
                send_message_safe(bot, user_id, "❌ Failed to create backup")
            
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Error in backup: {e}")
            bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    # ===== ADMIN COMMANDS =====
    @bot.message_handler(commands=['addadmin'])
    def addadmin_cmd(message: telebot.types.Message) -> None:
        """Add admin command."""
        try:
            user_id: int = message.from_user.id
            
            if not is_admin(user_id):
                send_message_safe(bot, user_id, "❌ Admin only")
                return
            
            text = "*👮 Add Admin*\n\n"
            text += "Send the user ID to promote:"
            
            msg = bot.send_message(user_id, text, parse_mode='Markdown')
            bot.register_next_step_handler(msg, handle_addadmin)
        except Exception as e:
            logger.error(f"Error in addadmin: {e}")
            send_message_safe(bot, message.from_user.id, "❌ Error")
    
    def handle_addadmin(message: telebot.types.Message) -> None:
        """Handle admin addition."""
        try:
            user_id: int = message.from_user.id
            
            try:
                new_admin_id: int = int(message.text)
            except ValueError:
                send_message_safe(bot, user_id, "❌ Invalid user ID")
                return
            
            success, msg_text = add_admin(new_admin_id)
            send_message_safe(bot, user_id, msg_text)
            
            if success:
                log_to_channel(bot, f"👮 New admin added: {new_admin_id}")
        except Exception as e:
            logger.error(f"Error adding admin: {e}")
            send_message_safe(bot, message.from_user.id, f"❌ Error: {str(e)}")
    
    # ===== CATCH ALL =====
    @bot.message_handler(func=lambda msg: True)
    def handle_all(message: telebot.types.Message) -> None:
        """Handle all other messages."""
        try:
            user_id: int = message.from_user.id
            
            text = "*👋 Welcome!*\n\n"
            text += "*Commands:*\n"
            text += "/start - 📖 Home\n"
            text += "/search - 🔍 Search\n"
            text += "/profile - 👤 Profile\n"
            text += "/bookmarks - 📌 Bookmarks\n"
            text += "/donate - 🎁 Donate\n"
            text += "/help - ❓ Help\n"
            
            if is_admin(user_id):
                text += "\n*Admin:*\n"
                text += "/edit - ⚙️ Edit Pages\n"
                text += "/stats - 📊 Statistics\n"
                text += "/broadcast - 📢 Broadcast\n"
                text += "/addadmin - 👮 Add Admin\n"
            
            markup = build_inline_keyboard([
                ("🏠 Home", "page:home"),
                ("🎁 Donate", "donate:menu")
            ])
            
            send_message_safe(bot, user_id, text, markup)
        except Exception as e:
            logger.error(f"Error in catch all: {e}")
    
    return bot

def ensure_files() -> None:
    """Initialize all data files."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(MEDIA_DIR, exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, 'backups'), exist_ok=True)
        
        if not os.path.exists(CONTENT_FILE):
            init_content: Dict[str, Any] = {
                "home": {
                    "unique_id": "home",
                    "title": "🏠 Welcome",
                    "text": "*Welcome to our ecosystem hub.*\n\nChoose a section below to explore.",
                    "buttons": [
                        {"type": "page", "label": "About Us", "target": "about"},
                        {"type": "page", "label": "Services", "target": "services"},
                        {"type": "page", "label": "Join Us", "target": "community"}
                    ],
                    "media": None,
                    "metadata": {
                        "category": "home",
                        "lang": "en",
                        "protected": False,
                        "tags": ["main", "entry"],
                        "access": "public"
                    },
                    "sections": []
                }
            }
            write_json(CONTENT_FILE, init_content)
        
        for file_path in [USERS_FILE, ANALYTICS_FILE, VERSIONS_FILE, FEEDBACK_FILE, BOOKMARKS_FILE, STATISTICS_FILE, DONATIONS_FILE]:
            if not os.path.exists(file_path):
                write_json(file_path, {})
        
        # Get default donate config
        get_donate_config()
        
        # Run migration
        migrate_users_data()
        
        logger.info("✅ All files initialized")
    except Exception as e:
        logger.error(f"Failed to ensure files: {e}")

def main() -> None:
    """Main function - Webhook mode for Vercel."""
    try:
        logger.info("=" * 60)
        logger.info("🤖 Advanced CMS Bot v3.0 - Vercel Webhook Edition")
        logger.info("=" * 60)
        logger.info(f"Bot Token: {CONFIG['bot_token'][:20]}...")
        logger.info(f"Admins: {CONFIG['admin_ids']}")
        logger.info(f"Log Channel: {LOG_CHANNEL_ID}")
        logger.info("=" * 60)
        
        bot = initialize_bot()
        logger.info("✅ Bot initialized successfully")
        
        # Create Flask app for webhook
        app = Flask(__name__)
        
        # Webhook endpoint
        @app.route('/', methods=['GET'])
        def index():
            return "✅ Bot is running", 200
        
        @app.route('/webhook', methods=['POST'])
        def webhook():
            """Receive updates from Telegram"""
            try:
                update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
                bot.process_new_updates([update])
                logger.info(f"✅ Update processed")
            except Exception as e:
                logger.error(f"❌ Webhook error: {e}")
            return "OK", 200
        
        # Set webhook with Telegram
        webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:5000')
        try:
            bot.remove_webhook()
            bot.set_webhook(url=f"{webhook_url}/webhook")
            logger.info(f"✅ Webhook set to: {webhook_url}/webhook")
        except Exception as e:
            logger.error(f"⚠️ Webhook setup warning: {e}")
        
        logger.info("🚀 Running in Webhook mode...")
        return app  # Return Flask app for Vercel
        
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Create app at module level for Vercel
app = None

def get_app():
    """Get or create Flask app"""
    global app
    if app is None:
        # Minimal Flask app for webhook
        app = Flask(__name__)
        bot = initialize_bot()
        
        @app.route('/', methods=['GET'])
        def index():
            return "✅ Bot is running", 200
        
        @app.route('/webhook', methods=['POST'])
        def webhook():
            try:
                update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
                bot.process_new_updates([update])
            except Exception as e:
                logger.error(f"Webhook error: {e}")
            return "OK", 200
        
        # Set webhook
        webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:5000')
        try:
            bot.remove_webhook()
            bot.set_webhook(url=f"{webhook_url}/webhook")
            logger.info(f"Webhook set to: {webhook_url}/webhook")
        except:
            pass
    
    return app

if __name__ == '__main__':
    main()
