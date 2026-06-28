import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/services/api-client"

export function useConversations(search?: string) {
  return useQuery({
    queryKey: ["conversations", search],
    queryFn: () => api.listConversations(search),
  })
}

export function useConversation(id: string | null) {
  return useQuery({
    queryKey: ["conversation", id],
    queryFn: () => api.getConversation(id!),
    enabled: !!id,
  })
}

export function useCreateConversation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (title?: string) => api.createConversation(title),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["conversations"] })
    },
  })
}

export function useUpdateConversation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...updates }: { id: string; title?: string; pinned?: boolean }) =>
      api.updateConversation(id, updates),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["conversations"] })
      qc.invalidateQueries({ queryKey: ["conversation"] })
    },
  })
}

export function useDeleteConversation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.deleteConversation(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["conversations"] })
    },
  })
}

export function useAddMessage() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ convId, role, content, citations }: { convId: string; role: string; content: string; citations?: string[] }) =>
      api.addMessage(convId, role, content, citations),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["conversation", data.conversation_id] })
      qc.invalidateQueries({ queryKey: ["conversations"] })
    },
  })
}

export function useGetMessages(convId: string | null) {
  return useQuery({
    queryKey: ["messages", convId],
    queryFn: () => api.getMessages(convId!),
    enabled: !!convId,
  })
}

export function useAddAttachment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ convId, documentId, filename, fileType }: { convId: string; documentId: string; filename: string; fileType: string }) =>
      api.addAttachment(convId, documentId, filename, fileType),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["conversation"] })
    },
  })
}

export function useRemoveAttachment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ convId, documentId }: { convId: string; documentId: string }) =>
      api.removeAttachment(convId, documentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["conversation"] })
    },
  })
}
