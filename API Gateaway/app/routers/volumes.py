from fastapi import APIRouter, Request
from app.proxy import proxy_request
from app.config import SERVICE_URLS

router = APIRouter(prefix="/volumes")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(path: str, request: Request):
    # Forward to Article Management Service which hosts /volumes
    return await proxy_request(SERVICE_URLS["articles"], request)
