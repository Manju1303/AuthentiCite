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

# Mount our backend FastAPI routes onto Gradio's FastAPI instance
demo.app.mount("/api/v1", fastapi_app)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)






