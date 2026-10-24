import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import { money } from '../format.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useCart } from '../context/CartContext.jsx'

export default function Checkout() {
  const { user } = useAuth()
  const { items, subtotal, clear } = useCart()
  const navigate = useNavigate()
  const [f, setF] = useState({ name: user?.name || '', zip: '', street: '', number: '', complement: '', district: '', city: '', state: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  if (items.length === 0) {
    return <div className="container page center"><h1>Seu carrinho está vazio</h1><Link to="/produtos" className="btn btn-primary">Ver produtos</Link></div>
  }

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    let order
    try {
      order = await api('/orders', {
        method: 'POST',
        body: { items: items.map((i) => ({ product_id: i.id, quantity: i.quantity })), shipping: f },
      })
      clear()
      const pay = await api(`/orders/${order.id}/pay`, { method: 'POST' })
      if (pay.mode === 'simulated') navigate(`/pagamento/${order.id}`)
      else window.location.href = pay.checkout_url
    } catch (err) {
      if (order) navigate(`/pedido/${order.id}`, { state: { notice: err.message } })
      else setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="container page">
      <h1>Finalizar compra</h1>
      <div className="cart">
        <form className="card form-grid" onSubmit={submit}>
          <h3 className="span2">Endereço de entrega</h3>
          {error && <p className="alert alert-bad span2" role="alert">{error}</p>}
          <label className="span2">Nome completo<input value={f.name} onChange={set('name')} required autoComplete="name" /></label>
          <label>CEP<input value={f.zip} onChange={set('zip')} required inputMode="numeric" maxLength={9} placeholder="00000-000" autoComplete="postal-code" /></label>
          <label>Estado (UF)<input value={f.state} onChange={set('state')} required maxLength={2} placeholder="SP" autoComplete="address-level1" /></label>
          <label className="span2">Rua<input value={f.street} onChange={set('street')} required autoComplete="address-line1" /></label>
          <label>Número<input value={f.number} onChange={set('number')} required /></label>
          <label>Complemento<input value={f.complement} onChange={set('complement')} /></label>
          <label>Bairro<input value={f.district} onChange={set('district')} /></label>
          <label>Cidade<input value={f.city} onChange={set('city')} required autoComplete="address-level2" /></label>
          <button className="btn btn-primary span2" disabled={busy}>{busy ? 'Criando pedido…' : 'Confirmar pedido e pagar'}</button>
        </form>
        <aside className="summary">
          <h3>Seu pedido</h3>
          {items.map((i) => (
            <div key={i.id} className="line"><span>{i.quantity}× {i.name}</span><span>{money(i.price * i.quantity)}</span></div>
          ))}
          <div className="line total"><span>Total</span><strong>{money(subtotal)}</strong></div>
          <p className="muted small">Pagamento em ambiente de teste: nenhuma cobrança real é feita.</p>
        </aside>
      </div>
    </div>
  )
}
