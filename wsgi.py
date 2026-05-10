"""
WSGI application wrapper for GTFS Route Planning API
Allows deployment with various WSGI servers (Gunicorn, uWSGI, etc.)
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import FastAPI app
from main import app

# WSGI application - compatible with Gunicorn, uWSGI, and other WSGI servers
# Usage with Gunicorn: gunicorn wsgi:app
# Usage with uWSGI: uwsgi --http :8000 --wsgi-file wsgi.py --callable app
# Usage with other servers: refer to server documentation

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload
    )
