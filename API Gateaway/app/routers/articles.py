from fastapi import APIRouter, Request, HTTPException
from app.proxy import proxy_request
from app.config import SERVICE_URLS
from app.security import get_current_user
import httpx

router = APIRouter(prefix="/articles")

@router.get("/{article_id}/reviewers")
async def get_article_reviewers(article_id: int, request: Request):
    """
    Aggregated endpoint: returns reviewers assigned to an article with deadlines.
    Access: editor or the article's responsible author.
    """
    # Validate JWT and get roles
    current = await get_current_user(request)

    # Authorization: allow editors; else verify responsible author via Articles service
    if "editor" not in (current.get("roles") or []):
        # Verify author access by calling Article Service's /my/{article_id}
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{SERVICE_URLS['articles']}/articles/my/{article_id}",
                headers={"Authorization": auth_header},
            )
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Article not found")
        if resp.status_code != 200:
            # 403 or any other -> forbid
            raise HTTPException(status_code=403, detail="Access denied")

    # Fetch reviews for article
    async with httpx.AsyncClient(timeout=10.0) as client:
        rev_resp = await client.get(f"{SERVICE_URLS['reviews']}/reviews/article/{article_id}")
    if rev_resp.status_code == 404:
        reviews = []
    elif rev_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch reviews")
    else:
        reviews = rev_resp.json() or []

    # Enrich reviewers with full info
    unique_ids = sorted({r.get("reviewer_id") for r in reviews if r.get("reviewer_id") is not None})
    profiles: dict[int, dict] = {}
    if unique_ids:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for uid in unique_ids:
                prof = None
                auth = None
                try:
                    p = await client.get(f"{SERVICE_URLS['users']}/users/{uid}")
                    if p.status_code == 200:
                        prof = p.json()
                except Exception:
                    prof = None
                try:
                    a = await client.get(f"{SERVICE_URLS['auth']}/auth/users/{uid}")
                    if a.status_code == 200:
                        auth = a.json()
                except Exception:
                    auth = None

                merged = {
                    "id": (prof or {}).get("id"),
                    "user_id": uid,
                    "full_name": (prof or {}).get("full_name") or (auth or {}).get("full_name"),
                    "phone": (prof or {}).get("phone"),
                    "organization": (prof or {}).get("organization") or (auth or {}).get("organization"),
                    "roles": (prof or {}).get("roles", []),
                    "preferred_language": (prof or {}).get("preferred_language"),
                    "is_active": (auth or {}).get("is_active"),
                    "username": (auth or {}).get("username"),
                    "email": (auth or {}).get("email"),
                    "first_name": (auth or {}).get("first_name"),
                    "last_name": (auth or {}).get("last_name"),
                    "institution": (auth or {}).get("institution"),
                }
                profiles[uid] = merged

    result_reviews = []
    for r in reviews:
        result_reviews.append({
            "review_id": r.get("id"),
            "reviewer_id": r.get("reviewer_id"),
            "deadline": r.get("deadline"),
            "status": r.get("status"),
            "reviewer": profiles.get(r.get("reviewer_id"))
        })

    return {"article_id": article_id, "reviews": result_reviews}

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(path: str, request: Request):
    return await proxy_request(SERVICE_URLS["articles"], request)
