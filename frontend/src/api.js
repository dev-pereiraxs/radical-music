const BASE = import.meta.env.VITE_API_URL || ''
export const TOKEN_KEY = 'rm_token'

export async function api(path, { method = 'GET', body, auth = true } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const token = localStorage.getItem(TOKEN_KEY)
  if (auth && token) headers.Authorization = `Bearer ${token}`

  let res
  try {
    res = await fetch(`${BASE}/api${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new Error('Não foi possível conectar ao servidor. Confira se o back-end (Flask) está rodando.')
  }
  let data = null
  try {
    data = await res.json()
  } catch {
    /* resposta sem corpo */
  }
  if (!res.ok) {
    const err = new Error(data?.error || 'Algo deu errado. Tente novamente.')
    err.status = res.status
    throw err
  }
  return data
}
