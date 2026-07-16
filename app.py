import uvicorn
import os
import sys

# Ensure the root directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create directories for uploads and outputs
os.makedirs("uploads/media", exist_ok=True)
os.makedirs("output", exist_ok=True)

if __name__ == "__main__":
    print("Starting Plagiarism Detection Backend on Hugging Face (Gradio Space)...")
    # Hugging Face Spaces require the app to listen on port 7860
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port)
