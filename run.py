import uvicorn
import os
import sys

# Ensure project root is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    print("Starting Research AI Backend Server...")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENV", "development").lower() == "development"
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=reload)

