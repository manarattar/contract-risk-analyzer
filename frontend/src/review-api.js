const base = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '') + '/api/v2'
const activeRequests = new Set()

export function abortRequests() {
  for (const controller of activeRequests) controller.abort()
  activeRequests.clear()
}

export async function request(token, path, { method = 'GET', body, signal, key, download = false } = {}) {
  const controller = new AbortController()
  const abort = () => controller.abort()
  signal?.addEventListener('abort', abort, { once: true })
  if (signal?.aborted) controller.abort()
  activeRequests.add(controller)
  try {
  const headers = { Authorization: `Bearer ${token}` }
  if (key) headers['Idempotency-Key'] = key
  if (body && !(body instanceof FormData)) headers['Content-Type'] = 'application/json'
  const response = await fetch(base + path, {
    method, headers, signal: controller.signal, cache: 'no-store',
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(typeof error.detail === 'string' ? error.detail : `Request failed (${response.status}). Please check your input or retry.`)
  }
  return await (download ? response.blob() : response.json())
  } finally {
    activeRequests.delete(controller)
    signal?.removeEventListener('abort', abort)
  }
}
