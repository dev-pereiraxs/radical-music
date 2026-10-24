import { useEffect, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { money } from '../format.js'

// Tela de pagamento SIMULADO (usada quando o back-end não tem MP_ACCESS_TOKEN).
export default function Payment() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [f, setF] = useState({ card_number: '', holder: '', expiry: '', cvv: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api(`/orders/${id}`).then(setOrder).catch((e) => setError(e.message))
  }, [id])

  if (order && order.status !== 'pending_payment') return <Navigate to={`/pedido/${id}`} replace />

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const r = await api('/payments/simulate', { method: 'POST', body: { order_id: Number(id), card_number: f.card_number } })
      if (r.status === 'paid') navigate(`/pedido/${id}`)
      else setError(r.message || 'Pagamento recusado.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container page">
      <h1>Pagamento</h1>
      <div className="cart">
        <form className="card form-grid" onSubmit={submit}>
          <p className="alert alert-info span2">
            <b>Ambiente de teste.</b> Nenhum dado é guardado e nada é cobrado. Use o cartão <b>4111 1111 1111 1111</b> para
            aprovar ou <b>4000 0000 0000 0002</b> para simular uma recusa.
          </p>
          {error && <p className="alert alert-bad span2" role="alert">{error}</p>}
          <label className="span2">Número do cartão<input value={f.card_number} onChange={set('card_number')} required inputMode="numeric" maxLength={23} placeholder="0000 0000 0000 0000" autoComplete="off" /></label>
          <label className="span2">Nome impresso no cartão<input value={f.holder} onChange={set('holder')} required autoComplete="off" /></label>
          <label>Validade<input value={f.expiry} onChange={set('expiry')} required placeholder="MM/AA" maxLength={5} autoComplete="off" /></label>
          <label>CVV<input value={f.cvv} onChange={set('cvv')} required inputMode="numeric" maxLength={4} autoComplete="off" /></label>
          <button className="btn btn-primary span2" disabled={busy || !order}>{busy ? 'Processando…' : `Pagar ${order ? money(order.total) : ''}`}</button>
        </form>
        <aside className="summary">
          <h3>Pedido #{id}</h3>
          {order?.items.map((i) => <div key={i.product_id} className="line"><span>{i.quantity}× {i.name}</span><span>{money(i.unit_price * i.quantity)}</span></div>)}
          {order && <div className="line total"><span>Total</span><strong>{money(order.total)}</strong></div>}
        </aside>
      </div>
    </div>
  )
}
