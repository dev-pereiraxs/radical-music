import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function AuthPage({ mode }) {
  const isRegister = mode === 'register'
  const { user, login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const from = location.state?.from || '/'

  if (user) return <Navigate to={from} replace />

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (isRegister) await register(form.name, form.email, form.password)
      else await login(form.email, form.password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container page">
      <form className="auth card" onSubmit={submit}>
        <h1>{isRegister ? 'Criar conta' : 'Entrar'}</h1>
        {location.state?.from && <p className="muted small">Faça login para continuar.</p>}
        {error && <p className="alert alert-bad" role="alert">{error}</p>}
        {isRegister && (
          <label>Nome<input value={form.name} onChange={set('name')} required minLength={2} autoComplete="name" /></label>
        )}
        <label>E-mail<input type="email" value={form.email} onChange={set('email')} required autoComplete="email" /></label>
        <label>Senha<input type="password" value={form.password} onChange={set('password')} required minLength={isRegister ? 6 : 1} autoComplete={isRegister ? 'new-password' : 'current-password'} /></label>
        <button className="btn btn-primary block" disabled={busy}>{busy ? 'Aguarde…' : isRegister ? 'Criar conta' : 'Entrar'}</button>
        <p className="center-text small">
          {isRegister ? <>Já tem conta? <Link to="/entrar" state={location.state} className="link">Entrar</Link></> : <>Novo por aqui? <Link to="/cadastro" state={location.state} className="link">Criar conta</Link></>}
        </p>
      </form>
    </div>
  )
}
