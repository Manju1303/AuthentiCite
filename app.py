import os
import sys
import gradio as gr

# Ensure the root directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.main import app as fastapi_app

# Create directories for uploads and outputs
os.makedirs("uploads/media", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Handle ZeroGPU environments (provides the required @spaces.GPU decorator)
try:
    import spaces
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# Create a simple Gradio landing page
with gr.Blocks() as demo:
    gr.Markdown("# 🛡️ AuthentiCite Backend API")
    gr.Markdown("The plagiarism detection and rewrite API is running successfully.")
    gr.Markdown("Access the interactive Swagger documentation at [/docs](/docs).")

    # Health check button (satisfies ZeroGPU @spaces.GPU requirement)
    health_output = gr.Textbox(label="API Status", interactive=False)
    health_btn = gr.Button("🔍 Check API Health")

    if GPU_AVAILABLE:
        @spaces.GPU(duration=5)
        def health_check():
            return "✅ AuthentiCite API is running — All systems operational"
    else:
        def health_check():
            return "✅ AuthentiCite API is running — All systems operational"

    health_btn.click(fn=health_check, inputs=[], outputs=[health_output])

# Access Gradio's internal FastAPI app and mount our plagiarism app under /api/v1
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
    # Let Gradio auto-detect the Hugging Face port, host, and SSL/protocol variables
    demo.launch()




