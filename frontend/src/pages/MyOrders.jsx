import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { STATUS, dateTime, money } from '../format.js'

export default function MyOrders() {
  const [orders, setOrders] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/orders').then(setOrders).catch((e) => setError(e.message))
  }, [])

  return (
    <div className="container page">
      <h1>Meus pedidos</h1>
      {error && <p className="alert alert-bad">{error}</p>}
      {orders === null && !error && <p className="muted">Carregando…</p>}
      {orders && orders.length === 0 && (
        <div className="empty"><h3>Você ainda não fez pedidos</h3><Link to="/produtos" className="btn btn-primary">Ver produtos</Link></div>
      )}
      <ul className="orders">
        {orders?.map((o) => {
          const st = STATUS[o.status] || { label: o.status, tone: 'info' }
          return (
            <li key={o.id} className="card order-row">
              <div>
                <Link to={`/pedido/${o.id}`} className="pcard-name">Pedido #{o.id}</Link>
                <p className="muted small">{dateTime(o.created_at)} · {o.items.reduce((s, i) => s + i.quantity, 0)} itens</p>
              </div>
              <span className={`badge badge-${st.tone}`}>{st.label}</span>
              <strong>{money(o.total)}</strong>
              <Link to={`/pedido/${o.id}`} className="btn btn-ghost btn-sm">Ver detalhes</Link>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
