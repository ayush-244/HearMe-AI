import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ..schemas.memory import (
    ExtractMemoryRequest, ExtractMemoryResponse,
    SearchMemoryRequest, SearchMemoryResponse,
    ListMemoryResponse, ConsolidateMemoryResponse,
    MemoryHealthResponse,
)
from ..services import get_services
from ..memory.memory_models import MemoryQuery

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/memory/extract", response_model=ExtractMemoryResponse)
async def extract_memory_endpoint(request: ExtractMemoryRequest):
    services = get_services()
    memory_engine = services.get("memory_engine")
    if memory_engine is None:
        raise HTTPException(status_code=503, detail="Memory engine not available")

    logger.info(
        "/memory/extract: user='%s', workspace='%s', text_len=%d",
        request.user_id, request.workspace_id, len(request.user_text),
    )

    try:
        result = memory_engine.process_conversation_turn(
            user_text=request.user_text,
            assistant_text=request.assistant_text,
            user_id=request.user_id,
            workspace_id=request.workspace_id,
        )
        return ExtractMemoryResponse(**result)
    except Exception as e:
        logger.error("/memory/extract error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Memory extraction failed: {str(e)}")


@router.get("/memory", response_model=ListMemoryResponse)
async def list_memories_endpoint(
    user_id: str = Query("", description="Filter by user"),
    workspace_id: str = Query("default", description="Filter by workspace"),
    memory_type: Optional[str] = Query(None, description="Filter by type (episodic/semantic/preference/working)"),
    include_working: bool = Query(False, description="Include working memories"),
):
    services = get_services()
    memory_engine = services.get("memory_engine")
    if memory_engine is None:
        raise HTTPException(status_code=503, detail="Memory engine not available")

    try:
        memories = memory_engine.get_memories(
            user_id=user_id,
            workspace_id=workspace_id,
            memory_type=memory_type,
            include_working=include_working,
        )
        return ListMemoryResponse(memories=[mem for mem in memories], count=len(memories))
    except Exception as e:
        logger.error("/memory list error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/search", response_model=SearchMemoryResponse)
async def search_memories_endpoint(request: SearchMemoryRequest):
    services = get_services()
    memory_engine = services.get("memory_engine")
    if memory_engine is None:
        raise HTTPException(status_code=503, detail="Memory engine not available")

    logger.info(
        "/memory/search: query='%s', workspace='%s', top_k=%d",
        request.query[:50], request.workspace_id, request.top_k,
    )

    try:
        memory_query = MemoryQuery(
            query=request.query,
            user_id=request.user_id,
            workspace_id=request.workspace_id,
            memory_types=request.memory_types,
            top_k=request.top_k,
            min_importance=request.min_importance,
            include_working=request.include_working,
        )
        result = memory_engine.retrieve_for_query(memory_query)
        return SearchMemoryResponse(**result)
    except Exception as e:
        logger.error("/memory/search error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Memory search failed: {str(e)}")


@router.delete("/memory/{memory_id}")
async def delete_memory_endpoint(memory_id: str):
    services = get_services()
    memory_engine = services.get("memory_engine")
    if memory_engine is None:
        raise HTTPException(status_code=503, detail="Memory engine not available")

    deleted = memory_engine.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory not found: {memory_id}")

    return {"deleted": True, "memory_id": memory_id}


@router.post("/memory/consolidate", response_model=ConsolidateMemoryResponse)
async def consolidate_memories_endpoint(
    user_id: str = Query("", description="User identifier"),
    workspace_id: str = Query("default", description="Workspace scope"),
):
    services = get_services()
    memory_engine = services.get("memory_engine")
    if memory_engine is None:
        raise HTTPException(status_code=503, detail="Memory engine not available")

    logger.info("/memory/consolidate: user='%s', workspace='%s'", user_id, workspace_id)

    try:
        result = memory_engine.consolidate(user_id=user_id, workspace_id=workspace_id)
        return ConsolidateMemoryResponse(**result)
    except Exception as e:
        logger.error("/memory/consolidate error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Consolidation failed: {str(e)}")


@router.get("/memory/health", response_model=MemoryHealthResponse)
async def memory_health_endpoint():
    services = get_services()
    memory_engine = services.get("memory_engine")
    if memory_engine is None:
        return MemoryHealthResponse(ready=False)

    try:
        health_info = memory_engine.health()
        return MemoryHealthResponse(**health_info)
    except Exception as e:
        logger.error("Memory health check failed: %s", e)
        return MemoryHealthResponse(ready=False)
