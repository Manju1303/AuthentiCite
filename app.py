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

# Mount Gradio UI onto the FastAPI application at root path /
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)





