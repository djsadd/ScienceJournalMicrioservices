import httpx
from fastapi import Request, Response

# Remove hop-by-hop headers so we do not forward connection-specific metadata
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def _filter_headers(headers) -> dict:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }


async def proxy_request(service_url: str, request: Request) -> Response:
    # Start with client headers minus hop-by-hop ones
    headers = dict(_filter_headers(request.headers))

    # If auth middleware/dependency resolved user, forward minimal identity
    user_id = getattr(request.state, "user_id", None)
    roles = getattr(request.state, "roles", None)
    if user_id is not None:
        headers["X-User-Id"] = str(user_id)
    if roles is not None:
        # Forward roles as a simple comma-separated list
        headers["X-User-Roles"] = ",".join(roles)

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.request(
            method=request.method,
            url=service_url + request.url.path,
            params=request.query_params,
            content=await request.body(),
            headers=headers,
            follow_redirects=False,
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=_filter_headers(resp.headers),
    )
