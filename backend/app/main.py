from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.llm.groq_provider import GroqProvider
from app.tools.registry import build_default_registry
from app.voice.voicebox_client import VoiceboxClient

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

tool_registry = build_default_registry()
llm_provider = GroqProvider(tool_registry=tool_registry)
voicebox_client = VoiceboxClient()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str

class SpeakRequest(BaseModel):
    text: str
    profile: str = "testsubj1"

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    reply = await llm_provider.complete(request.message)
    return ChatResponse(reply=reply)


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        llm_provider.stream(request.message),
        media_type="text/plain",
    )
@app.post("/chat/agent")
async def chat_agent(request: ChatRequest) -> ChatResponse:
    reply = await llm_provider.complete_with_tools(request.message)
    return ChatResponse(reply=reply)

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> dict[str, str]:
    audio_bytes = await file.read()
    text = await llm_provider.transcribe(
        audio_bytes, file.filename or "recording.webm"
    )
    return {"text": text}

@app.post("/speak")
async def speak(request: SpeakRequest) -> dict:
    return await voicebox_client.speak(request.text, request.profile)

@app.get("/profiles")
async def list_profiles() -> list[dict]:
    return await voicebox_client.list_profiles()