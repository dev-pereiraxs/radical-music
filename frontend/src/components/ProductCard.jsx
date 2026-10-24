import { useState } from 'react'
import { Link } from 'react-router-dom'
import { money } from '../format.js'
import { useCart } from '../context/CartContext.jsx'
import { ProductImage } from './ProductArt.jsx'

export default function ProductCard({ p }) {
  const { add } = useCart()
  const [added, setAdded] = useState(false)
  const out = p.stock <= 0

  const onAdd = () => {
    add(p, 1)
    setAdded(true)
    setTimeout(() => setAdded(false), 1400)
  }

  return (
    <article className="pcard">
      <Link to={`/produto/${p.id}`} className="pcard-img" aria-label={p.name}>
        <ProductImage p={p} />
        {out && <span className="tag tag-out">Esgotado</span>}
        {!out && p.stock <= 3 && <span className="tag tag-low">Últimas unidades</span>}
      </Link>
      <div className="pcard-body">
        <span className="pcard-brand">{p.brand || p.category.name}</span>
        <Link to={`/produto/${p.id}`} className="pcard-name">{p.name}</Link>
        <strong className="price">{money(p.price)}</strong>
        <span className="muted small">em até 10x de {money(p.price / 10)}</span>
        <button className="btn btn-primary btn-sm" onClick={onAdd} disabled={out}>
          {out ? 'Indisponível' : added ? 'Adicionado!' : 'Adicionar ao carrinho'}
        </button>
      </div>
    </article>
  )
}
