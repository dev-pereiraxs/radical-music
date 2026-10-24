import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function RequireAuth({ admin = false, children }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <div className="container page"><p className="muted">Carregando…</p></div>
  if (!user) return <Navigate to="/entrar" state={{ from: location.pathname + location.search }} replace />
  if (admin && !user.is_admin) {
    return (
      <div className="container page">
        <h1>Acesso restrito</h1>
        <p className="muted">Esta área é exclusiva para administradores da loja.</p>
      </div>
    )
  }
  return children
}
