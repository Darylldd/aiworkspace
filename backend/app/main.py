from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.db.database import init_db
from app.llm.groq_provider import GroqProvider
from app.memory.conversation_store import ConversationStore
from app.tools.registry import ToolRegistry, build_default_registry
from app.voice.voicebox_client import VoiceboxClient
from app.workspace.boundary import WorkspaceBoundary
from app.workspace.manager import WorkspaceManager, WorkspaceValidationError

load_dotenv()
init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

workspace_manager = WorkspaceManager()
voicebox_client = VoiceboxClient()
conversation_store = ConversationStore()

_current_tool_registry: ToolRegistry | None = None
_current_llm_provider: GroqProvider | None = None
_current_workspace_id: int | None = None
_active_conversation_id: int | None = None


def _rebuild_provider_for_workspace(workspace_id: int, path: str) -> None:
    global _current_tool_registry, _current_llm_provider, _current_workspace_id, _active_conversation_id
    boundary = WorkspaceBoundary(root=path)
    _current_tool_registry = build_default_registry(boundary, workspace_id)
    _current_llm_provider = GroqProvider(tool_registry=_current_tool_registry)
    _current_workspace_id = workspace_id
    _active_conversation_id = conversation_store.create_conversation(workspace_id)


def _get_llm_provider() -> GroqProvider:
    if _current_llm_provider is None:
        raise HTTPException(
            status_code=400,
            detail="No active workspace. Create and select a workspace first.",
        )
    return _current_llm_provider


existing_active = workspace_manager.get_active()
if existing_active is not None:
    _rebuild_provider_for_workspace(existing_active.id, existing_active.path)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


class SpeakRequest(BaseModel):
    text: str
    profile: str = "testsubj1"


class WorkspaceCreateRequest(BaseModel):
    name: str
    path: str


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    provider = _get_llm_provider()
    reply = await provider.complete(request.message)
    return ChatResponse(reply=reply)


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    provider = _get_llm_provider()
    return StreamingResponse(
        provider.stream(request.message),
        media_type="text/plain",
    )


@app.post("/chat/agent")
async def chat_agent(request: ChatRequest) -> ChatResponse:
    provider = _get_llm_provider()

    history = []
    if _active_conversation_id is not None:
        stored_messages = conversation_store.get_messages(_active_conversation_id)
        history = [{"role": m.role, "content": m.content} for m in stored_messages]

    reply = await provider.complete_with_tools(request.message, history=history)

    if _active_conversation_id is not None:
        conversation_store.add_message(_active_conversation_id, "user", request.message)
        conversation_store.add_message(_active_conversation_id, "assistant", reply)

    return ChatResponse(reply=reply)


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> dict[str, str]:
    provider = _get_llm_provider()
    audio_bytes = await file.read()
    text = await provider.transcribe(
        audio_bytes, file.filename or "recording.webm"
    )
    return {"text": text}


@app.get("/profiles")
async def list_profiles() -> list[dict]:
    return await voicebox_client.list_profiles()


@app.post("/speak")
async def speak(request: SpeakRequest) -> dict:
    return await voicebox_client.speak(request.text, request.profile)


@app.get("/workspaces")
def list_workspaces() -> list[dict]:
    return [
        {"id": w.id, "name": w.name, "path": w.path, "is_active": w.is_active}
        for w in workspace_manager.list_all()
    ]


@app.post("/workspaces")
def create_workspace(request: WorkspaceCreateRequest) -> dict:
    try:
        workspace = workspace_manager.create(request.name, request.path)
    except WorkspaceValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return {"id": workspace.id, "name": workspace.name, "path": workspace.path}


@app.post("/workspaces/{workspace_id}/activate")
def activate_workspace(workspace_id: int) -> dict:
    try:
        workspace = workspace_manager.set_active(workspace_id)
    except WorkspaceValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))

    _rebuild_provider_for_workspace(workspace.id, workspace.path)

    return {"id": workspace.id, "name": workspace.name, "path": workspace.path, "is_active": True}