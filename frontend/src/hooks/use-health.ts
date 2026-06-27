import { useQuery } from "@tanstack/react-query"
import { api } from "@/services/api-client"

export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: () => api.health() })
}

export function useSearchHealth() {
  return useQuery({ queryKey: ["search-health"], queryFn: () => api.searchHealth() })
}

export function useKnowledgeHealth() {
  return useQuery({ queryKey: ["knowledge-health"], queryFn: () => api.knowledgeHealth() })
}

export function useVectorStoreHealth() {
  return useQuery({ queryKey: ["vectorstore-health"], queryFn: () => api.vectorStoreHealth() })
}

export function useAllHealth() {
  const health = useHealth()
  const search = useSearchHealth()
  const knowledge = useKnowledgeHealth()
  const vector = useVectorStoreHealth()
  const memory = useQuery({ queryKey: ["memory-health-v2"], queryFn: () => api.memoryHealth() })
  return { health, search, knowledge, vector, memory }
}
