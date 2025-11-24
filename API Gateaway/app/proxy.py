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
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.request(
            method=request.method,
            url=service_url + request.url.path,
            params=request.query_params,
            content=await request.body(),
            headers=_filter_headers(request.headers),
            follow_redirects=False,
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=_filter_headers(resp.headers),
    )
