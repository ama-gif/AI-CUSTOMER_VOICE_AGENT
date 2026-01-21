# main_api.py
from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException
from fastapi.responses import FileResponse
import uvicorn
from agent import SupportAgent
from llm_loader import load_llm
from tools.stt_whisper import transcribe_audio_bytes
import uuid, os

# Gracefully handle optional TTS import
try:
    from tools.tts_coqui import synthesize_text_to_wav
except ImportError as e:
    print(f"Warning: TTS not available: {e}")
    def synthesize_text_to_wav(text: str):
        """Fallback TTS function when TTS is not available"""
        return None

app = FastAPI(title="AI Customer Support Agent API")

# Lazy load LLM and agent to avoid blocking on startup
_llm = None
_agent = None

def get_agent():
    global _llm, _agent
    if _agent is None:
        try:
            _llm = load_llm()
            _agent = SupportAgent(llm=_llm)
        except Exception as e:
            print(f"Error loading LLM: {e}")
            return None
    return _agent

@app.post("/session/start")
def start():
    agent = get_agent()
    if not agent:
        raise HTTPException(status_code=500, detail="LLM not available")
    sid = str(uuid.uuid4())
    agent.start_session(sid)
    return {"session_id": sid}

@app.post("/session/{session_id}/message")
def send_message(session_id: str, payload: dict):
    agent = get_agent()
    if not agent:
        raise HTTPException(status_code=500, detail="LLM not available")
    text = payload.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    return agent.add_user_message(session_id, text)

@app.post("/session/{session_id}/audio")
async def send_audio(session_id: str, file: UploadFile = File(...)):
    agent = get_agent()
    if not agent:
        raise HTTPException(status_code=500, detail="LLM not available")
    audio_bytes = await file.read()
    text = transcribe_audio_bytes(audio_bytes, format=file.filename.split(".")[-1])
    res = agent.add_user_message(session_id, text)
    # optionally produce tts
    wav_path = synthesize_text_to_wav(res["reply"])
    return {"transcript": text, "reply": res["reply"], "wav": wav_path}

@app.post("/session/{session_id}/save")
def save(session_id: str):
    agent = get_agent()
    if not agent:
        raise HTTPException(status_code=500, detail="LLM not available")
    return agent.save_chat(session_id)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    agent = get_agent()
    if not agent:
        await websocket.close(code=1008, reason="LLM not available")
        return
    await websocket.accept()
    agent.start_session(session_id)
    try:
        while True:
            data = await websocket.receive_text()
            resp = agent.add_user_message(session_id, data)
            # also send TTS file path if desired
            await websocket.send_text(resp["reply"])
    except Exception:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)