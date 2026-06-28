import re
from typing import Dict, List, Pattern, Tuple

GREETING_PATTERNS: List[Pattern] = [
    re.compile(r"^(hello|hi|hey|greetings|good\s*(morning|afternoon|evening|day)|sup|yo|howdy)\b", re.IGNORECASE),
    re.compile(r"^(what'?s\s+up|nice\s+to\s+meet\s+you)\b", re.IGNORECASE),
    re.compile(r"^(morning|afternoon|evening)[\s!.]*$", re.IGNORECASE),
]

SMALL_TALK_PATTERNS: List[Pattern] = [
    re.compile(r"\bhow\s+are\s+you\b", re.IGNORECASE),
    re.compile(r"\bhow'?s\s+it\s+going\b", re.IGNORECASE),
    re.compile(r"\bwho\s+are\s+you\b", re.IGNORECASE),
    re.compile(r"\bwhere\s+are\s+you\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+can\s+you\s+do\b", re.IGNORECASE),
    re.compile(r"\b(thank\w*|thanks|thx)\b", re.IGNORECASE),
    re.compile(r"\b(bye|goodbye|see\s+(you|ya)|later|cya)\b", re.IGNORECASE),
    re.compile(r"\b(cool|awesome|nice|great|wonderful|amazing|fantastic)\s*!*$", re.IGNORECASE),
    re.compile(r"\b(how'?s\s+(your\s+)?(day|weekend|week|morning|afternoon|evening))\b", re.IGNORECASE),
    re.compile(r"^(ok|okay|alright|sure|fine|got\s*it|understood)\s*[.!]*$", re.IGNORECASE),
    re.compile(r"\b(what'?s\s+up|not\s+much|nothing\s+much)\b", re.IGNORECASE),
    re.compile(r"\bi'?m?\s*(doing\s+)?(good|fine|great|okay|alright)\s*[,!]?\s*(you\s+)?\?*$", re.IGNORECASE),
]

PERSONAL_MEMORY_PATTERNS: List[Pattern] = [
    re.compile(r"\b(who\s+am\s+i|what\s+is\s+my\s+name|do\s+you\s+know\s+me)\b", re.IGNORECASE),
    re.compile(r"\b(what\s+do\s+you\s+know\s+about\s+me|tell\s+me\s+about\s+myself)\b", re.IGNORECASE),
    re.compile(r"\b(my\s+name\s+is|i\s+am\s+called)\b", re.IGNORECASE),
    re.compile(r"\b(what\s+is\s+my|what\s+are\s+my|my\s+\w+\s+is)\b", re.IGNORECASE),
    re.compile(r"\b(where\s+(do|did)\s+i|when\s+(did|was)\s+i|how\s+(old|tall)\s+am\s+i)\b", re.IGNORECASE),
    re.compile(r"\b(remember\s+(me|my|about\s+me)|do\s+you\s+remember)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+are\s+my\s+(skills|interest|hobbies|likes|dislikes|preferences)\b", re.IGNORECASE),
    re.compile(r"\bwhere\s+(do\s+i|did\s+i)\s+(study|work|live|go\s+to\s+school)\b", re.IGNORECASE),
    re.compile(r"\b(what'?s?\s+(my\s+)?(name|age|email|phone|address|birthday))\b", re.IGNORECASE),
]

DOCUMENT_QUESTION_PATTERNS: List[Pattern] = [
    re.compile(r"\b(summarize|summarise|sum up|overview|give\s+me\s+the\s+gist)\b", re.IGNORECASE),
    re.compile(r"\b(wha[td]\s+does\s+(this|my|the|that)\s+(document|file|pdf|resume|paper|article))\b", re.IGNORECASE),
    re.compile(r"\b(compare|contrast|difference\s+between)\s+(the\s+)?(documents?|files?|papers?|resumes?|articles?|reports?|sections?|pages?)\b", re.IGNORECASE),
    re.compile(r"\b(what\s+skills|what\s+experience|what\s+education)\b", re.IGNORECASE),
    re.compile(r"\b(page\s+\d+|section\s+\d+|chapter\s+\d+)\b", re.IGNORECASE),
    re.compile(r"\b(what\s+does\s+page|on\s+page|from\s+the\s+document)\b", re.IGNORECASE),
    re.compile(r"\b(in\s+this\s+(document|file|paper|article|resume|report))\b", re.IGNORECASE),
    re.compile(r"\baccording\s+to\s+(the|this|my|that)\s+(document|file|paper|resume)\b", re.IGNORECASE),
    re.compile(r"\b(documents?|files?|papers?|resume|articles?)\s+(related|about|regarding|mentioning)\b", re.IGNORECASE),
]

GENERAL_AI_PATTERNS: List[Pattern] = [
    re.compile(r"\b(explain|describe|define|what\s+is|what\s+are|how\s+does|how\s+do)\s+(?!my|this|that\s+(document|file|paper|resume))", re.IGNORECASE),
    re.compile(r"\bdifference\s+between\s+\w+\s+and\s+\w+\b", re.IGNORECASE),
    re.compile(r"\b(tell\s+me\s+about|what\s+is|what\s+are|define)\s+(?!my|the\s+document|this\s+file)", re.IGNORECASE),
    re.compile(r"\b(how\s+(does|do|can|would|should|could|will))\s+(?!i|you|we|my|this\s+document)", re.IGNORECASE),
    re.compile(r"\b(why\s+(is|are|does|do|can|would|should|could|will))\b", re.IGNORECASE),
    re.compile(r"\b(what\s+(is|are|does|do)\s+the\s+(difference|meaning|purpose|definition|concept))\b", re.IGNORECASE),
]

FOLLOW_UP_PATTERNS: List[Pattern] = [
    re.compile(r"^(explain\s+more|tell\s+me\s+more|continue|go\s+on|keep\s+going|elaborate|expand)\b", re.IGNORECASE),
    re.compile(r"^(can\s+you\s+(elaborate|expand|clarify|simplify|explain\s+that))\b", re.IGNORECASE),
    re.compile(r"^(what\s+about|how\s+about)\s+(that|this|it|the\s+rest)\s*\?*$", re.IGNORECASE),
    re.compile(r"^(and\s+then\?|so\?|then\?)$", re.IGNORECASE),
    re.compile(r"^(i\s+see|makes\s+sense|interesting)\s*,?\s*(but|and|so)\b", re.IGNORECASE),
    re.compile(r"\b(simplify|simplified|simpler|easier|dumb\s+it\s+down)\b", re.IGNORECASE),
    re.compile(r"^(what\s+does\s+that\s+mean|what\s+do\s+you\s+mean)\b", re.IGNORECASE),
    re.compile(r"\b(what\s+else|anything\s+else|more\s+details|further)\b", re.IGNORECASE),
    re.compile(r"^(can\s+you\s+(repeat|say\s+that\s+again))\b", re.IGNORECASE),
]

SHORT_QUERY_THRESHOLD = 3

PERSONAL_PRONOUN_PATTERNS: List[Pattern] = [
    re.compile(r"\b(my|mine|me|i'?m|i'?ve|i'?ll|i'?d)\b", re.IGNORECASE),
]

DOCUMENT_REFERENCE_PATTERNS: List[Pattern] = [
    re.compile(r"\b(resume|document|file|pdf|paper|article|book|report|notes|slide)\b", re.IGNORECASE),
    re.compile(r"\b(upload|attached|saved|stored)\b", re.IGNORECASE),
]

PERSONAL_MEMORY_QUESTION_WORDS: set = {
    "who", "whom", "whose",
}

DOCUMENT_QUESTION_WORDS: set = {
    "summarize", "summarise", "compare", "contrast",
    "outline", "highlight", "list", "extract",
}
