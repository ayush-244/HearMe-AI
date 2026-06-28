import json
import logging
import time
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

REASONING_STAGES = [
    ("thinking", "Thinking..."),
    ("searching_documents", "Searching documents..."),
    ("searching_memories", "Searching memories..."),
    ("reasoning", "Reasoning..."),
    ("writing", "Writing response..."),
]

STAGE_EVENT = "stage"
TOKEN_EVENT = "token"
DONE_EVENT = "done"
ERROR_EVENT = "error"
CITATION_EVENT = "citation"


def stage_event(stage: str, label: str) -> str:
    return f"data: {json.dumps({'type': STAGE_EVENT, 'stage': stage, 'label': label})}\n\n"


def token_event(token: str) -> str:
    return f"data: {json.dumps({'type': TOKEN_EVENT, 'token': token})}\n\n"


def done_event(result: Dict[str, Any]) -> str:
    return f"data: {json.dumps({'type': DONE_EVENT, 'result': result})}\n\n"


def error_event(message: str) -> str:
    return f"data: {json.dumps({'type': ERROR_EVENT, 'message': message})}\n\n"


def citation_event(citations: List[str], sources: List[Dict]) -> str:
    return f"data: {json.dumps({'type': CITATION_EVENT, 'citations': citations, 'sources': sources})}\n\n"


class StreamingChatService:
    def __init__(self, llm: Any):
        self._llm = llm
        logger.info("StreamingChatService initialized")

    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        try:
            stream = self._llm.stream(prompt)
            for chunk in stream:
                if hasattr(chunk, "content"):
                    content = chunk.content
                else:
                    content = str(chunk)
                if content:
                    yield token_event(content)
        except Exception as e:
            logger.error("Streaming LLM error: %s", e, exc_info=True)
            yield error_event(str(e))

    def generate_stages(self, intent: str, search_docs: bool, search_mem: bool) -> List[Dict[str, str]]:
        stages = [{"stage": "thinking", "label": "Thinking..."}]

        if search_docs:
            stages.append({"stage": "searching_documents", "label": "Searching documents..."})

        if search_mem:
            stages.append({"stage": "searching_memories", "label": "Searching memories..."})

        stages.append({"stage": "writing", "label": "Writing response..."})

        return stages
