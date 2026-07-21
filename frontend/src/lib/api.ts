import { request, type RequestOptions } from '@/lib/http'
import { supabase } from '@/lib/supabase'

export type MeResponse = {
  id: string
  email: string
}

export type ThreadResponse = {
  id: string
  title: string
}

export type ThreadListItem = {
  id: string
  title: string
  updatedAt: string
}

export type ThreadListResponse = {
  threads: ThreadListItem[]
}

export type UIMessagePart = {
  type: string
  text?: string
  data?: unknown
}

export type MessageCitation = {
  marker: number
  chunkId: string
  documentId: string
  quote: string | null
  company: string
  ticker: string
  form: string
  fiscalYear: string
  filingDate: string
  section: string | null
  sourceUrl: string
  excerpt: string
}

export type RefusalReason = 'insufficient_evidence' | 'no_advice'

export type MessageRefusal = {
  reasons: RefusalReason[]
}

export type UIChatMessage = {
  id: string
  role: 'user' | 'assistant' | 'system'
  parts: UIMessagePart[]
}

export type ThreadHistoryResponse = {
  id: string
  title: string
  messages: UIChatMessage[]
}

export type Passage = {
  chunkId: string
  documentId: string
  chunkIndex: number
  text: string
  section: string | null
  company: string
  ticker: string
  form: string
  fiscalYear: string
  filingDate: string
  sourceUrl: string
}

export type CitationContextResponse = {
  passage: Passage
  neighbors: Passage[]
}

export async function getAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? null
}

async function withAuth<T>(
  path: string,
  options: Omit<RequestOptions, 'accessToken'> = {},
): Promise<T> {
  return request<T>(path, {
    ...options,
    accessToken: await getAccessToken(),
  })
}

export const api = {
  get: <T>(path: string, options?: Omit<RequestOptions, 'accessToken' | 'method' | 'body'>) =>
    withAuth<T>(path, { ...options, method: 'GET' }),

  post: <T>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, 'accessToken' | 'method' | 'body'>,
  ) => withAuth<T>(path, { ...options, method: 'POST', body }),

  put: <T>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, 'accessToken' | 'method' | 'body'>,
  ) => withAuth<T>(path, { ...options, method: 'PUT', body }),

  patch: <T>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, 'accessToken' | 'method' | 'body'>,
  ) => withAuth<T>(path, { ...options, method: 'PATCH', body }),

  delete: <T>(path: string, options?: Omit<RequestOptions, 'accessToken' | 'method' | 'body'>) =>
    withAuth<T>(path, { ...options, method: 'DELETE' }),

  me: () => api.get<MeResponse>('/me'),

  createThread: (title?: string) =>
    api.post<ThreadResponse>('/threads', title ? { title } : {}),

  listThreads: () => api.get<ThreadListResponse>('/threads'),

  getThread: (threadId: string) => api.get<ThreadHistoryResponse>(`/threads/${threadId}`),

  deleteThread: (threadId: string) => api.delete<void>(`/threads/${threadId}`),

  getCitationContext: (chunkId: string) =>
    api.get<CitationContextResponse>(`/citations/${chunkId}/context`),
}
