import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/services/api-client"

export function useMemories(params?: { user_id?: string; workspace_id?: string; memory_type?: string; include_working?: boolean }) {
  return useQuery({ queryKey: ["memories", params], queryFn: () => api.listMemories(params) })
}

export function useSearchMemories() {
  return useMutation({ mutationFn: (payload: { query: string; user_id?: string; top_k?: number }) => api.searchMemories(payload) })
}

export function useDeleteMemory() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (id: string) => api.deleteMemory(id), onSuccess: () => qc.invalidateQueries({ queryKey: ["memories"] }) })
}

export function useConsolidateMemories() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (params?: { user_id?: string }) => api.consolidateMemories(params), onSuccess: () => qc.invalidateQueries({ queryKey: ["memories"] }) })
}

export function useMemoryHealth() {
  return useQuery({ queryKey: ["memory-health"], queryFn: () => api.memoryHealth() })
}
