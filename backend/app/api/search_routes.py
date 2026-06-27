import logging
from fastapi import APIRouter, HTTPException
from ..schemas.search import SearchRequest, SearchResponse, SearchHealthResponse
from ..services import get_services
from ..retrieval.search_models import SearchQuery

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    services = get_services()
    search_engine = services.get("search_engine")
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not available")

    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(
        "/search request: query='%s', workspace=%s, top_k=%d",
        query[:80], request.workspace_id, request.top_k,
    )

    search_query = SearchQuery(
        text=query,
        workspace_id=request.workspace_id,
        top_k=request.top_k,
        min_score=request.min_score,
        filters=request.filters,
        language=request.language,
        document_type=request.document_type,
        document_ids=request.document_ids,
    )

    try:
        result = search_engine.search(search_query)
        response_dict = result.to_dict()
        logger.info(
            "/search result: chunks=%d, latency=%.2fms",
            len(result.results), result.processing_time_ms,
        )
        return SearchResponse(**response_dict)
    except Exception as e:
        logger.error("/search error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/health", response_model=SearchHealthResponse)
async def search_health_endpoint():
    services = get_services()
    search_engine = services.get("search_engine")
    if search_engine is None:
        return SearchHealthResponse(ready=False)

    try:
        health_info = search_engine.health()
        return SearchHealthResponse(
            ready=health_info.get("ready", False),
            embedding_model_loaded=health_info.get("embedding_model_loaded", False),
            vector_store_healthy=health_info.get("vector_store_healthy", False),
            keyword_backend=health_info.get("keyword_backend", ""),
            ranking_weights=health_info.get("ranking_weights", {}),
            statistics=health_info.get("statistics", {}),
        )
    except Exception as e:
        logger.error("Search health check failed: %s", e)
        return SearchHealthResponse(ready=False)
