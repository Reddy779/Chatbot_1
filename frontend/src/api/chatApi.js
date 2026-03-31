import axios from 'axios'

const BASE = '/api'

export const api = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
})

export const createSession  = (userId, title) => api.post('/sessions', { user_id: userId, title })
export const getSessions     = (userId)        => api.get(`/sessions/${userId}`)
export const getFacts        = (userId)        => api.get(`/memory/facts/${userId}`)
export const getSummaries    = (userId)        => api.get(`/memory/summaries/${userId}`)
export const deleteFact      = (factId)        => api.delete(`/memory/facts/${factId}`)

export async function streamChat(sessionId, userId, message, onChunk, onDone, onError) {
  try {
    const res = await fetch(`${BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, user_id: userId, message }),
    })

    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const reader  = res.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value, { stream: true })
      for (const line of text.split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          const json = JSON.parse(line.slice(6))
          if (json.done)  { onDone();        return }
          if (json.error) { onError(json);   return }
          if (json.chunk)   onChunk(json.chunk)
        } catch { /* skip malformed */ }
      }
    }
  } catch (err) {
    onError({ error: err.message })
  }
}