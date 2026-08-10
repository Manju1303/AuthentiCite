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
def zerogpu_health_check(text: str = "ping"):
    return f"✅ AuthentiCite API running on ZeroGPU — Status: OK ({text})"

with gr.Blocks(title="AuthentiCite API") as demo:
    gr.Markdown("# 🛡️ AuthentiCite Backend API")
    gr.Markdown("The plagiarism detection, paper generator, and rewrite API is running successfully.")

    inp = gr.Textbox(label="Health Ping", value="System Status")
    out = gr.Textbox(label="ZeroGPU Status")
    btn = gr.Button("🔍 Check API & ZeroGPU Health")
    btn.click(fn=zerogpu_health_check, inputs=[inp], outputs=[out])

# Mount Gradio UI onto the main FastAPI application at /ui
app = gr.mount_gradio_app(fastapi_app, demo, path="/ui")

@fastapi_app.get("/", include_in_schema=False)
def root_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/ui")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=False)







