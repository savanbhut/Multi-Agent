const API_BASE = 'http://localhost:8000'

export async function runResearch(topic, maxSources) {
  const response = await fetch(`${API_BASE}/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, max_sources: maxSources }),
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Request failed: ${response.status}`)
  }

  return response.json()
}