export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  citations?: string[]
  sources?: Source[]
  timestamp: string
}

export interface Source {
  document_id: string
  title: string
  sections: string[]
  pages: number[]
}

export interface KnowledgeQuery {
  question: string
  workspace_id?: string
  conversation_id?: string
  top_k?: number
  min_score?: number
  language?: string
}

export interface KnowledgeResponse {
  question: string
  answer: string
  citations: string[]
  sources: Source[]
  processing_time_ms: number
  retrieval_time_ms: number
  generation_time_ms: number
  chunk_count: number
  context_token_estimate: number
  validation_passed: boolean
  guardrail_triggered: boolean
  knowledge_gap: boolean
  conversation_id: string
}

export interface SearchQuery {
  text: string
  workspace_id?: string
  top_k?: number
  min_score?: number
  language?: string
  document_type?: string
  document_ids?: string[]
}

export interface SearchResult {
  chunk_id: string
  document_id: string
  text: string
  title: string
  section: string
  page: number
  score: number
  semantic_score: number
  keyword_score: number
  metadata_score: number
  language: string
  document_type: string
  workspace_id: string
  chunk_index: number
  word_count: number
  keywords: string[]
}

export interface SearchResponse {
  query: string
  results: SearchResult[]
  citations: string[]
  statistics: SearchStatistics
  processing_time_ms: number
}

export interface SearchStatistics {
  total_chunks_searched: number
  semantic_chunks_retrieved: number
  keyword_chunks_scored: number
  final_chunks_returned: number
  avg_semantic_score: number
  avg_keyword_score: number
  avg_final_score: number
  semantic_latency_ms: number
  keyword_latency_ms: number
  ranking_latency_ms: number
  total_latency_ms: number
}

export interface Document {
  id: string
  filename: string
  file_type: string
  size: number
  status: string
  upload_time: string
  storage_path?: string
  failed_stage?: string
}

export interface MemoryEntry {
  memory_id: string
  user_id: string
  workspace_id: string
  type: "semantic" | "episodic" | "preference" | "working"
  content: string
  summary: string
  importance: number
  confidence: number
  created_at: string
  updated_at: string
  last_accessed: string
  access_count: number
  source: string
  pinned: boolean
}

export interface MemoryExtractResponse {
  extracted_count: number
  stored_count: number
  rejected_count: number
  updated_count: number
  working_memory_id: string | null
  processing_time_ms: number
}

export interface MemorySearchResponse {
  memories: MemoryEntry[]
  count: number
  processing_time_ms: number
}

export interface HealthResponse {
  ready: boolean
  [key: string]: unknown
}

export interface Settings {
  theme: "dark" | "light" | "system"
  model: string
  memory_threshold: number
  search_top_k: number
  reasoning_max_chunks: number
  language: string
  workspace_id: string
}
