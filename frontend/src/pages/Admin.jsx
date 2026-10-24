import { Fragment, useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import { STATUS, dateTime, money } from '../format.js'
import { ProductImage } from '../components/ProductArt.jsx'

function Summary() {
  const [s, setS] = useState(null)
  useEffect(() => {
    api('/admin/summary').then(setS).catch(() => {})
  }, [])
  if (!s) return null
  const cards = [
    ['Receita (pedidos pagos)', money(s.revenue)],
    ['Pedidos', s.orders],
    ['Aguardando pagamento', s.pending],
    ['Clientes', s.customers],
    ['Produtos ativos', s.products],
  ]
  return (
    <>
      <div className="stats">
        {cards.map(([label, value]) => (
          <div key={label} className="stat"><span className="muted small">{label}</span><strong>{value}</strong></div>
        ))}
      </div>
      {s.low_stock.length > 0 && (
        <p className="alert alert-warn">
          <b>Estoque baixo:</b> {s.low_stock.map((p) => `${p.name} (${p.stock})`).join(' · ')}
        </p>
      )}
    </>
  )
}

function StockCell({ p, onChange }) {
  const [v, setV] = useState(String(p.stock))
  const [busy, setBusy] = useState(false)
  useEffect(() => setV(String(p.stock)), [p.stock])
  const dirty = v !== String(p.stock)
  const save = async () => {
    setBusy(true)
    try {
      onChange(await api(`/admin/products/${p.id}/stock`, { method: 'PATCH', body: { stock: Number(v) } }))
    } catch (e) {
      window.alert(e.message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="stock-cell">
      <input type="number" min="0" value={v} onChange={(e) => setV(e.target.value)} aria-label={`Estoque de ${p.name}`} />
      {dirty && <button className="btn btn-primary btn-sm" onClick={save} disabled={busy}>Salvar</button>}
    </div>
  )
}

function ProductForm({ product, cats, onClose, onSaved }) {
  const [f, setF] = useState({
    name: product?.name || '', brand: product?.brand || '', category_id: product?.category.id || cats[0]?.id || '',
    price: product?.price ?? '', stock: product?.stock ?? 0, image: product?.image || '', description: product?.description || '',
    featured: product?.featured || false, active: product?.active ?? true,
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const path = product ? `/admin/products/${product.id}` : '/admin/products'
      await api(path, { method: product ? 'PUT' : 'POST', body: f })
      onSaved()
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="modal-back" onClick={onClose}>
      <form className="modal card form-grid" onClick={(e) => e.stopPropagation()} onSubmit={submit} role="dialog" aria-label="Produto">
        <h3 className="span2">{product ? 'Editar produto' : 'Novo produto'}</h3>
        {error && <p className="alert alert-bad span2" role="alert">{error}</p>}
        <label className="span2">Nome<input value={f.name} onChange={set('name')} required minLength={3} /></label>
        <label>Marca<input value={f.brand} onChange={set('brand')} /></label>
        <label>Categoria
          <select value={f.category_id} onChange={set('category_id')} required>
            {cats.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </label>
        <label>Preço (R$)<input value={f.price} onChange={set('price')} required inputMode="decimal" /></label>
        <label>Estoque<input type="number" min="0" value={f.stock} onChange={set('stock')} required /></label>
        <label className="span2">Imagem (caminho em /public, ex.: /products/foto.webp)<input value={f.image} onChange={set('image')} /></label>
        <label className="span2">Descrição<textarea rows={3} value={f.description} onChange={set('description')} /></label>
        <label className="check"><input type="checkbox" checked={f.featured} onChange={set('featured')} /> Destaque na página inicial</label>
        <label className="check"><input type="checkbox" checked={f.active} onChange={set('active')} /> Visível na loja</label>
        <div className="span2 row end">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancelar</button>
          <button className="btn btn-primary" disabled={busy}>{busy ? 'Salvando…' : 'Salvar'}</button>
        </div>
      </form>
    </div>
  )
}

function ProductsTab() {
  const [list, setList] = useState([])
  const [cats, setCats] = useState([])
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState(null) // null = fechado, {} = novo
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')

  const load = useCallback(
    () => api(`/admin/products?search=${encodeURIComponent(search)}`).then(setList).catch((e) => setError(e.message)),
    [search],
  )
  useEffect(() => {
    const t = setTimeout(load, 250)
    return () => clearTimeout(t)
  }, [load])
  useEffect(() => {
    api('/filters', { auth: false }).then((d) => setCats(d.categories)).catch(() => {})
  }, [])

  const replace = (p) => setList((cur) => cur.map((x) => (x.id === p.id ? p : x)))
  const remove = async (p) => {
    if (!window.confirm(`Excluir "${p.name}"?`)) return
    try {
      const r = await api(`/admin/products/${p.id}`, { method: 'DELETE' })
      setMsg(r.message)
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <section>
      <div className="toolbar">
        <input className="search-admin" placeholder="Buscar produto…" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Buscar produto" />
        <button className="btn btn-primary btn-sm" onClick={() => setEditing({})}>+ Novo produto</button>
      </div>
      {msg && <p className="alert alert-ok">{msg}</p>}
      {error && <p className="alert alert-bad">{error}</p>}
      <div className="table-wrap">
        <table>
          <thead><tr><th>Produto</th><th>Categoria</th><th>Preço</th><th>Estoque</th><th>Status</th><th /></tr></thead>
          <tbody>
            {list.map((p) => (
              <tr key={p.id} className={p.active ? '' : 'inactive'}>
                <td><div className="prod-cell"><span className="thumb"><ProductImage p={p} /></span><span><b>{p.name}</b><br /><span className="muted small">{p.brand}</span></span></div></td>
                <td>{p.category.name}</td>
                <td>{money(p.price)}</td>
                <td><StockCell p={p} onChange={replace} /></td>
                <td>{p.active ? (p.stock <= 3 ? <span className="badge badge-warn">Estoque baixo</span> : <span className="badge badge-ok">Ativo</span>) : <span className="badge badge-bad">Oculto</span>}</td>
                <td className="nowrap">
                  <button className="link-btn" onClick={() => setEditing(p)}>Editar</button>
                  <button className="link-btn danger" onClick={() => remove(p)}>Excluir</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editing && <ProductForm product={editing.id ? editing : null} cats={cats} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); setMsg('Produto salvo.'); load() }} />}
    </section>
  )
}

function OrdersTab() {
  const [orders, setOrders] = useState([])
  const [status, setStatus] = useState('')
  const [open, setOpen] = useState(null)
  const [error, setError] = useState('')

  const load = useCallback(
    () => api(`/admin/orders${status ? `?status=${status}` : ''}`).then(setOrders).catch((e) => setError(e.message)),
    [status],
  )
  useEffect(() => { load() }, [load])

  const change = async (o, next) => {
    setError('')
    try {
      await api(`/admin/orders/${o.id}/status`, { method: 'PATCH', body: { status: next } })
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <section>
      <div className="toolbar">
        <label>Status{' '}
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todos</option>
            {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </label>
      </div>
      {error && <p className="alert alert-bad">{error}</p>}
      <div className="table-wrap">
        <table>
          <thead><tr><th>Pedido</th><th>Cliente</th><th>Data</th><th>Total</th><th>Status</th></tr></thead>
          <tbody>
            {orders.length === 0 && <tr><td colSpan="5" className="muted">Nenhum pedido.</td></tr>}
            {orders.map((o) => (
              <Fragment key={o.id}>
                <tr>
                  <td><button className="link-btn" onClick={() => setOpen(open === o.id ? null : o.id)} aria-expanded={open === o.id}>#{o.id} {open === o.id ? '▲' : '▼'}</button></td>
                  <td>{o.customer.name}<br /><span className="muted small">{o.customer.email}</span></td>
                  <td>{dateTime(o.created_at)}</td>
                  <td>{money(o.total)}</td>
                  <td>
                    <select value={o.status} onChange={(e) => change(o, e.target.value)} disabled={o.status === 'cancelled'} aria-label={`Status do pedido ${o.id}`}>
                      {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                    </select>
                  </td>
                </tr>
                {open === o.id && (
                  <tr className="detail-row">
                    <td colSpan="5">
                      {o.items.map((i) => <div key={i.product_id}>{i.quantity}× {i.name} <span className="muted">({money(i.unit_price)})</span></div>)}
                      <p className="muted small">Entrega: {o.shipping.name}, {o.shipping.street}, {o.shipping.number} – {o.shipping.city}/{o.shipping.state}, CEP {o.shipping.zip}{o.payment_provider ? ` · Pagamento: ${o.payment_provider}` : ''}</p>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default function Admin() {
  const [tab, setTab] = useState('products')
  return (
    <div className="container page">
      <h1>Painel administrativo</h1>
      <Summary />
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === 'products'} className={tab === 'products' ? 'on' : ''} onClick={() => setTab('products')}>Produtos e estoque</button>
        <button role="tab" aria-selected={tab === 'orders'} className={tab === 'orders' ? 'on' : ''} onClick={() => setTab('orders')}>Pedidos</button>
      </div>
      {tab === 'products' ? <ProductsTab /> : <OrdersTab />}
    </div>
  )
}
