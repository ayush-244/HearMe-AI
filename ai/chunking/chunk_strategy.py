import logging
from typing import Optional
from .fixed_chunker import FixedChunker
from .section_chunker import SectionChunker
from .semantic_chunker import SemanticChunker

logger = logging.getLogger(__name__)


STRATEGY_MAP = {
    "research_paper": "section",
    "resume": "section",
    "book": "section",
    "report": "section",
    "invoice": "section",
    "presentation": "section",
    "manual": "section",
    "article": "section",
    "notes": "semantic",
    "unknown": "fixed",
}

FILE_TYPE_STRATEGY = {
    "txt": "fixed",
    "markdown": "semantic",
}


def select_strategy(
    document_type: str = "unknown",
    file_type: Optional[str] = None,
) -> str:
    strategy = STRATEGY_MAP.get(document_type, "fixed")
    if strategy == "fixed" and file_type:
        strategy = FILE_TYPE_STRATEGY.get(file_type, "fixed")
    logger.info("Selected chunking strategy: %s (type=%s, file=%s)", strategy, document_type, file_type)
    return strategy


def create_chunker(strategy: str, chunk_size: int = 500, overlap: int = 50):
    if strategy == "section":
        logger.debug("Creating SectionChunker (size=%d, overlap=%d)", chunk_size, overlap)
        return SectionChunker(chunk_size=chunk_size, overlap=overlap)
    elif strategy == "semantic":
        logger.debug("Creating SemanticChunker")
        return SemanticChunker()
    else:
        logger.debug("Creating FixedChunker (size=%d, overlap=%d)", chunk_size, overlap)
        return FixedChunker(chunk_size=chunk_size, overlap=overlap)
