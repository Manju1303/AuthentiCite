import os
import sys
import gradio as gr
import spaces

# Ensure the root directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.main import app as fastapi_app

# Create directories for uploads and outputs
os.makedirs("uploads/media", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Top-level @spaces.GPU function required by ZeroGPU environment
@spaces.GPU(duration=5)
def zerogpu_health_check():
    return "✅ AuthentiCite API running on ZeroGPU — All systems operational"

with gr.Blocks() as demo:
    gr.Markdown("# 🛡️ AuthentiCite Backend API")
    gr.Markdown("The plagiarism detection and rewrite API is running successfully.")
    gr.Markdown("Access the interactive Swagger documentation at [/docs](/docs).")

    health_output = gr.Textbox(label="API Status", interactive=False)
    health_btn = gr.Button("🔍 Check API Health")
    health_btn.click(fn=zerogpu_health_check, inputs=[], outputs=[health_output])

# Mount Gradio UI onto the FastAPI application at root path /
app = gr.mount_gradio_app(fastapi_app, demo, path="/")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)





