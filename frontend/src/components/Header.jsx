import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useCart } from '../context/CartContext.jsx'
import { CartIcon, SearchIcon, UserIcon } from './Icons.jsx'

const MenuIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
)
const CloseIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
)

export default function Header() {
  const { user, logout } = useAuth()
  const { count } = useCart()
  const navigate = useNavigate()
  const location = useLocation()
  const [q, setQ] = useState('')
  const [cats, setCats] = useState([])
  const [menu, setMenu] = useState(false) // menu do usuário (desktop)
  const [drawer, setDrawer] = useState(false) // menu lateral (celular)

  useEffect(() => {
    api('/filters', { auth: false }).then((d) => setCats(d.categories)).catch(() => {})
  }, [])

  // Fecha os menus ao trocar de página.
  useEffect(() => {
    setMenu(false)
    setDrawer(false)
  }, [location.pathname, location.search])

  // Menu lateral aberto: trava a rolagem da página e fecha com Esc.
  useEffect(() => {
    if (!drawer) return
    const onKey = (e) => e.key === 'Escape' && setDrawer(false)
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', onKey)
    }
  }, [drawer])

  // Se a tela crescer (ex.: celular girado), o menu lateral não faz mais sentido.
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 901px)')
    const onChange = (e) => e.matches && setDrawer(false)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  const search = (e) => {
    e.preventDefault()
    navigate(`/produtos?busca=${encodeURIComponent(q.trim())}`)
  }
  const closeDrawer = () => setDrawer(false)
  // NavLink ignora a parte "?categoria=" do endereço, então o destaque é calculado aqui.
  const currentCat = location.pathname === '/produtos' ? new URLSearchParams(location.search).get('categoria') || '' : null

  return (
    <>
      <header className="header">
        <div className="container header-main">
          <button className="menu-btn" onClick={() => setDrawer(true)} aria-label="Abrir menu" aria-expanded={drawer} aria-controls="menu-mobile">
            <MenuIcon />
          </button>
          <Link to="/" className="brand" aria-label="Radical Music, página inicial">
            <img src="/logo-icon.png" alt="" />
            <span>Radical<b>Music</b></span>
          </Link>

          <form className="search" onSubmit={search} role="search">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar violão, guitarra, cordas…" aria-label="Buscar produtos" />
            <button type="submit" aria-label="Buscar"><SearchIcon /></button>
          </form>

          <nav className="actions" aria-label="Conta e carrinho">
            {user ? (
              <div className="usermenu">
                <button className="link-btn" onClick={() => setMenu(!menu)} aria-expanded={menu}>
                  <UserIcon /> <span className="hide-sm">{user.name.split(' ')[0]}</span>
                </button>
                {menu && (
                  <div className="dropdown" onClick={() => setMenu(false)}>
                    <Link to="/meus-pedidos">Meus pedidos</Link>
                    {user.is_admin && <Link to="/admin">Painel administrativo</Link>}
                    <button onClick={logout}>Sair</button>
                  </div>
                )}
              </div>
            ) : (
              <Link to="/entrar" className="link-btn"><UserIcon /> <span className="hide-sm">Entrar</span></Link>
            )}
            <Link to="/carrinho" className="link-btn cart-link" aria-label={`Carrinho com ${count} itens`}>
              <CartIcon />
              {count > 0 && <span className="cart-badge">{count}</span>}
            </Link>
          </nav>
        </div>
        <nav className="catbar" aria-label="Categorias">
          <div className="container">
            <Link to="/produtos" className={currentCat === '' ? 'active' : ''}>Todos</Link>
            {cats.map((c) => (
              <Link key={c.id} to={`/produtos?categoria=${c.slug}`} className={currentCat === c.slug ? 'active' : ''}>{c.name}</Link>
            ))}
          </div>
        </nav>
      </header>

      {/* Fica fora do <header> porque o desfoque do cabeçalho prenderia o painel dentro dele. */}
      <div className={`drawer-back${drawer ? ' open' : ''}`} onClick={closeDrawer}>
        <nav className="drawer" id="menu-mobile" aria-label="Menu principal" onClick={(e) => e.stopPropagation()}>
          <div className="drawer-head">
            <img src="/logo.png" alt="Radical Music" />
            <button className="drawer-close" onClick={closeDrawer} aria-label="Fechar menu"><CloseIcon /></button>
          </div>

          <h4>Categorias</h4>
          <Link to="/produtos" onClick={closeDrawer} className={currentCat === '' ? 'active' : ''}>Todos os produtos</Link>
          {cats.map((c) => (
            <Link key={c.id} to={`/produtos?categoria=${c.slug}`} onClick={closeDrawer} className={currentCat === c.slug ? 'active' : ''}>
              {c.name}
            </Link>
          ))}

          <h4>Conta</h4>
          {user ? (
            <>
              <Link to="/meus-pedidos" onClick={closeDrawer}>Meus pedidos</Link>
              {user.is_admin && <Link to="/admin" onClick={closeDrawer}>Painel administrativo</Link>}
              <button onClick={() => { closeDrawer(); logout() }}>Sair</button>
            </>
          ) : (
            <>
              <Link to="/entrar" onClick={closeDrawer}>Entrar</Link>
              <Link to="/cadastro" onClick={closeDrawer}>Criar conta</Link>
            </>
          )}
        </nav>
      </div>
    </>
  )
}