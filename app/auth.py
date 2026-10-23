import hmac
import os
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import TOKEN_ENV

security_scheme = HTTPBearer(auto_error=False)

async def require_auth(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    """Validates the Bearer token against AGENT_API_TOKEN using constant-time comparison."""
    # Check if a token was attempted via query parameters - reject immediately with 403
    for query_param in ["token", "access_token", "api_key", "key", "auth"]:
        if query_param in request.query_params:
            raise HTTPException(status_code=403, detail="Forbidden")

    raw_auth = request.headers.get("authorization", "")
    if not raw_auth:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Reject non-Bearer schemes like Basic
    if not raw_auth.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Forbidden")

    token_candidate = raw_auth[7:].strip()
    if not token_candidate:
        raise HTTPException(status_code=403, detail="Forbidden")

    expected = os.environ.get(TOKEN_ENV, "")
    if not expected:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not hmac.compare_digest(token_candidate.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Forbidden")

    return token_candidate
