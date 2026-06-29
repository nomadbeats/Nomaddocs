"""
Vercel Webhook Handler
Receives updates from Telegram and processes them
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_app

app = get_app()

# For Vercel
def handler(request):
    """Vercel serverless function handler"""
    return app(request)
