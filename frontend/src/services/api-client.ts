import { API_BASE } from "@/lib/constants"
import type {
  ChatMessage,
  Document,
  HealthResponse,
  KnowledgeQuery,
  KnowledgeResponse,
  MemoryEntry,
  MemoryExtractResponse,
  MemorySearchResponse,
  SearchQuery,
  SearchResponse,
} from "@/types"

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = "ApiError"
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error")
    throw new ApiError(res.status, text)
  }
  return res.json()
}

export const api = {
  // Health
  health: () => request<HealthResponse>("/health"),

  // Chat
  sendMessage: (message: string, language = "auto", history: ChatMessage[] = []) =>
    request<{ reply: string; sentiment: string; confidence: number; detected_language: string; language_name: string }>(
      "/chat",
      { method: "POST", body: JSON.stringify({ message, language, history }) }
    ),

  analyze: (message: string, language = "auto") =>
    request<Record<string, unknown>>("/analyze", {
      method: "POST",
      body: JSON.stringify({ message, language }),
    }),

  // Documents
  uploadDocument: async (file: File) => {
    const form = new FormData()
    form.append("file", file)
    const res = await fetch(`${API_BASE}/documents/upload`, { method: "POST", body: form })
    if (!res.ok) {
      const text = await res.text().catch(() => "Upload failed")
      throw new ApiError(res.status, text)
    }
    return res.json()
  },

  getDocuments: () => request<{ documents: Document[]; count: number }>("/documents"),

  getDocument: (id: string) => request<Document>(`/documents/${id}`),

  deleteDocument: (id: string) => request<{ status: string }>(`/documents/${id}`, { method: "DELETE" }),

  extractDocument: (id: string) =>
    request<{ document_id: string; status: string }>(`/documents/${id}/extract`, { method: "POST" }),

  analyzeDocument: (id: string) =>
    request<Record<string, unknown>>(`/documents/${id}/analyze`, { method: "POST" }),

  chunkDocument: (id: string) =>
    request<{ status: string; strategy: string; chunk_count: number }>(`/documents/${id}/chunk`, { method: "POST" }),

  embedDocument: (id: string) =>
    request<Record<string, unknown>>(`/documents/${id}/embed`, { method: "POST" }),

  indexDocument: (id: string) =>
    request<{ status: string; vectors: number; collection: string }>(`/documents/${id}/index`, { method: "POST" }),

  deindexDocument: (id: string) =>
    request<{ status: string }>(`/documents/${id}/index`, { method: "DELETE" }),

  retryDocument: (id: string) =>
    request<{ status: string; document_id: string; stage: string; message: string }>(`/documents/${id}/retry`, { method: "POST" }),

  getFailedDetails: (id: string) =>
    request<{ status: string; document_id: string; failed_stage: string; message: string }>(`/documents/${id}/failed`),

  // Search
  search: (query: SearchQuery) =>
    request<SearchResponse>("/search", { method: "POST", body: JSON.stringify(query) }),

  searchHealth: () => request<HealthResponse>("/search/health"),

  // Knowledge
  knowledgeQuery: (query: KnowledgeQuery) =>
    request<KnowledgeResponse>("/knowledge/chat", { method: "POST", body: JSON.stringify(query) }),

  knowledgeHealth: () => request<HealthResponse>("/knowledge/health"),

  // Memory
  extractMemory: (payload: { user_text: string; assistant_text?: string; user_id?: string; workspace_id?: string }) =>
    request<MemoryExtractResponse>("/memory/extract", { method: "POST", body: JSON.stringify(payload) }),

  listMemories: (params?: { user_id?: string; workspace_id?: string; memory_type?: string; include_working?: boolean }) => {
    const search = new URLSearchParams()
    if (params?.user_id) search.set("user_id", params.user_id)
    if (params?.workspace_id) search.set("workspace_id", params.workspace_id)
    if (params?.memory_type) search.set("memory_type", params.memory_type)
    if (params?.include_working) search.set("include_working", "true")
    return request<{ memories: MemoryEntry[]; count: number }>(`/memory?${search}`)
  },

  searchMemories: (payload: { query: string; user_id?: string; workspace_id?: string; top_k?: number }) =>
    request<MemorySearchResponse>("/memory/search", { method: "POST", body: JSON.stringify(payload) }),

  deleteMemory: (id: string) => request<{ deleted: boolean }>(`/memory/${id}`, { method: "DELETE" }),

  consolidateMemories: (params?: { user_id?: string; workspace_id?: string }) => {
    const search = new URLSearchParams()
    if (params?.user_id) search.set("user_id", params.user_id)
    return request<{ consolidated_count: number }>(`/memory/consolidate?${search}`, { method: "POST" })
  },

  memoryHealth: () => request<HealthResponse>("/memory/health"),

  // Vector Store
  vectorStoreHealth: () => request<HealthResponse>("/vectorstore/health"),
}
