import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api.js'
import { STATUS, cep, dateTime, money } from '../format.js'

export default function Order() {
  const { id } = useParams()
  const [sp] = useSearchParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [notice, setNotice] = useState(location.state?.notice || '')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        let o = await api(`/orders/${id}`)
        // Retorno do Mercado Pago: confirma o pagamento direto na API deles.
        const pid = sp.get('payment_id') || sp.get('collection_id')
        if (o.status === 'pending_payment' && pid && /^\d+$/.test(pid)) {
          const r = await api(`/orders/${id}/confirm-payment`, { method: 'POST', body: { payment_id: pid } })
          o = r.order
          if (r.result === 'pending') setNotice('Seu pagamento está em análise. Atualizaremos o pedido assim que for aprovado.')
          if (r.result === 'rejected') setNotice('O pagamento foi recusado. Você pode tentar novamente abaixo.')
        }
        if (alive) setOrder(o)
      } catch (e) {
        if (alive) setError(e.message)
      }
    })()
    return () => { alive = false }
  }, [id])

  const payAgain = async () => {
    setBusy(true)
    setError('')
    try {
      const pay = await api(`/orders/${id}/pay`, { method: 'POST' })
      if (pay.mode === 'simulated') navigate(`/pagamento/${id}`)
      else window.location.href = pay.checkout_url
    } catch (e) {
      setError(e.message)
      setBusy(false)
    }
  }
  const cancel = async () => {
    if (!window.confirm('Cancelar este pedido?')) return
    setBusy(true)
    try {
      setOrder(await api(`/orders/${id}/cancel`, { method: 'POST' }))
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  if (error && !order) return <div className="container page"><p className="alert alert-bad">{error}</p><Link to="/meus-pedidos" className="link">← Meus pedidos</Link></div>
  if (!order) return <div className="container page"><p className="muted">Carregando…</p></div>

  const st = STATUS[order.status] || { label: order.status, tone: 'info' }
  const s = order.shipping

  return (
    <div className="container page">
      <div className="section-head">
        <h1>Pedido #{order.id}</h1>
        <span className={`badge badge-${st.tone}`}>{st.label}</span>
      </div>
      {order.status === 'paid' && <p className="alert alert-ok">Pagamento confirmado! Obrigado pela compra.</p>}
      {notice && <p className="alert alert-info">{notice}</p>}
      {error && <p className="alert alert-bad" role="alert">{error}</p>}

      <div className="cart">
        <section className="card">
          <h3>Itens</h3>
          {order.items.map((i) => (
            <div key={i.product_id} className="line"><span>{i.quantity}× {i.name}</span><span>{money(i.unit_price * i.quantity)}</span></div>
          ))}
          <div className="line total"><span>Total</span><strong>{money(order.total)}</strong></div>
        </section>
        <aside className="summary">
          <h3>Entrega</h3>
          <p>{s.name}<br />{s.street}, {s.number}{s.complement && ` – ${s.complement}`}<br />{s.district && `${s.district} · `}{s.city}/{s.state}<br />CEP {cep(s.zip)}</p>
          <p className="muted small">Feito em {dateTime(order.created_at)}</p>
          {order.status === 'pending_payment' && (
            <>
              <button className="btn btn-primary block" onClick={payAgain} disabled={busy}>Pagar agora</button>
              <button className="btn btn-ghost block" onClick={cancel} disabled={busy}>Cancelar pedido</button>
            </>
          )}
          <Link to="/meus-pedidos" className="link center-text">← Meus pedidos</Link>
        </aside>
      </div>
    </div>
  )
}
