import uuid
import logging
from typing import Dict, Any, List, Optional, Literal
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict

from app.config import AGENT_TITLE, AGENT_VERSION
from app.auth import require_auth
from app.agent import execute_agent

logger = logging.getLogger("support_agent")

app = FastAPI(
    title=AGENT_TITLE,
    version=AGENT_VERSION,
    servers=[],  # CertifyAI specifies not to set servers
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers ensuring no traces or internal details leak
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request schema or payload size."}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred."}
    )

# Request and Response schemas strictly conforming to CertifyAI requirements
class ChatRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=8000, description="Customer chat input message")
    session_id: Optional[str] = Field(None, max_length=128, description="Optional conversation session ID")

    model_config = ConfigDict(extra="ignore")

class ToolCallRecord(BaseModel):
    tool: str
    args: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str

class ChatResponse(BaseModel):
    output: str
    finish_reason: Literal[
        "complete",
        "policy_refusal",
        "max_steps_reached",
        "timeout",
        "error",
        "length",
        "content_filter",
        "tool_calls",
    ]
    trace_id: str
    steps_taken: int
    cost_usd: float
    tool_calls: List[ToolCallRecord]

class HealthResponse(BaseModel):
    status: str

# 1. /chat MUST be the first route registered so it appears first in the OpenAPI spec
@app.post(
    "/chat",
    response_model=ChatResponse,
    operation_id="chat",
    summary="Process customer support chat message"
)
async def chat(req: ChatRequest, token: str = Depends(require_auth)) -> ChatResponse:
    """Processes customer support requests with real data tools and security guardrails."""
    trace_id = str(uuid.uuid4())
    result = await execute_agent(user_input=req.input, session_id=req.session_id, trace_id=trace_id)
    return ChatResponse(
        output=result.output,
        finish_reason=result.finish_reason, # type: ignore
        trace_id=result.trace_id,
        steps_taken=result.steps_taken,
        cost_usd=result.cost_usd,
        tool_calls=[
            ToolCallRecord(
                tool=tc.tool,
                args=tc.args,
                result=tc.result,
                error=tc.error,
                timestamp=tc.timestamp
            ) for tc in result.tool_calls
        ]
    )

# 2. /health is registered second, remains public, and answers in under a second without model calls
@app.get(
    "/health",
    response_model=HealthResponse,
    operation_id="health",
    summary="Agent health status check"
)
async def health() -> HealthResponse:
    """Returns immediate health status without calling language model."""
    return HealthResponse(status="ok")

# 3. Mount frontend static files so the UI is served directly at the root URL
import os
from fastapi.staticfiles import StaticFiles

_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")

