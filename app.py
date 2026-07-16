import os
import sys
import gradio as gr

# Ensure the root directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.main import app as fastapi_app

# Create directories for uploads and outputs
os.makedirs("uploads/media", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Create a simple Gradio landing page
with gr.Blocks() as demo:
    gr.Markdown("# 🛡️ AuthentiCite Backend API")
    gr.Markdown("The plagiarism detection and rewrite API is running successfully.")
    gr.Markdown("Access the interactive Swagger documentation at [/docs](/docs).")

# Access Gradio's internal FastAPI app and mount our plagiarism app
# We can mount the plagiarism API under `/` or a subpath.
# To keep the API endpoints at /api/v1, we can mount it directly to demo.app
demo.app.mount("/api/v1", fastapi_app)

# Allow FastAPI's docs to be accessible
@demo.app.get("/docs", include_in_schema=False)
async def get_docs():
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url="/api/v1/openapi.json", title="AuthentiCite API Docs")

@demo.app.get("/api/v1/openapi.json", include_in_schema=False)
async def get_openapi():
    return fastapi_app.openapi()

if __name__ == "__main__":
    # Call launch() as expected by Hugging Face's Gradio Space runner
    port = int(os.getenv("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)


