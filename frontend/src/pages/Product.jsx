import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { money } from '../format.js'
import { useCart } from '../context/CartContext.jsx'
import { ProductImage } from '../components/ProductArt.jsx'

export default function Product() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { add } = useCart()
  const [p, setP] = useState(null)
  const [error, setError] = useState('')
  const [qty, setQty] = useState(1)
  const [added, setAdded] = useState(false)

  useEffect(() => {
    setP(null)
    setError('')
    setQty(1)
    api(`/products/${id}`, { auth: false }).then(setP).catch((e) => setError(e.message))
  }, [id])

  if (error) return <div className="container page"><p className="alert alert-bad">{error}</p><Link to="/produtos" className="link">← Voltar ao catálogo</Link></div>
  if (!p) return <div className="container page"><p className="muted">Carregando…</p></div>

  const out = p.stock <= 0
  const onAdd = () => {
    add(p, qty)
    setAdded(true)
    setTimeout(() => setAdded(false), 1400)
  }

  return (
    <div className="container page">
      <p className="crumbs"><Link to="/produtos">Produtos</Link> / <Link to={`/produtos?categoria=${p.category.slug}`}>{p.category.name}</Link></p>
      <div className="detail">
        <div className="detail-img"><ProductImage p={p} eager /></div>
        <div className="detail-info">
          {p.brand && <span className="pcard-brand">{p.brand}</span>}
          <h1>{p.name}</h1>
          <strong className="price big">{money(p.price)}</strong>
          <span className="muted">em até 10x de {money(p.price / 10)}</span>
          <p className={out ? 'stock out' : p.stock <= 3 ? 'stock low' : 'stock'}>
            {out ? 'Produto esgotado' : p.stock <= 3 ? `Restam apenas ${p.stock} unidades` : 'Em estoque'}
          </p>
          <p className="desc">{p.description}</p>
          {!out && (
            <div className="row buy">
              <div className="qty" role="group" aria-label="Quantidade">
                <button onClick={() => setQty(Math.max(1, qty - 1))} aria-label="Diminuir">−</button>
                <span>{qty}</span>
                <button onClick={() => setQty(Math.min(p.stock, qty + 1))} aria-label="Aumentar">+</button>
              </div>
              <button className="btn btn-primary" onClick={onAdd}>{added ? 'Adicionado!' : 'Adicionar ao carrinho'}</button>
              <button className="btn btn-ghost" onClick={() => { add(p, qty); navigate('/carrinho') }}>Comprar agora</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
