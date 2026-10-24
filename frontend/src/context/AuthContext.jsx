import { createContext, useContext, useEffect, useState } from 'react'
import { api, TOKEN_KEY } from '../api.js'

const Ctx = createContext(null)
export const useAuth = () => useContext(Ctx)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(!!localStorage.getItem(TOKEN_KEY))

  useEffect(() => {
    if (!localStorage.getItem(TOKEN_KEY)) return
    api('/auth/me')
      .then((d) => setUser(d.user))
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setLoading(false))
  }, [])

  const save = (d) => {
    localStorage.setItem(TOKEN_KEY, d.token)
    setUser(d.user)
  }
  const login = async (email, password) =>
    save(await api('/auth/login', { method: 'POST', body: { email, password }, auth: false }))
  const register = async (name, email, password) =>
    save(await api('/auth/register', { method: 'POST', body: { name, email, password }, auth: false }))
  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
  }

  return <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>
}
