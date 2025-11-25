from fastapi import APIRouter, Depends, Request
from app.proxy import proxy_request
from app.config import SERVICE_URLS
from app.security import get_current_user

router = APIRouter(prefix="/users")


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy(path: str, request: Request, current_user=Depends(get_current_user)):
    # get_current_user ensures the request is authenticated and populates request.state
    return await proxy_request(SERVICE_URLS["users"], request)
