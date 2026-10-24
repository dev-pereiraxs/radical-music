import { Link, useNavigate } from 'react-router-dom'
import { money } from '../format.js'
import { useCart } from '../context/CartContext.jsx'
import { ProductImage } from '../components/ProductArt.jsx'

export default function Cart() {
  const { items, setQty, remove, subtotal, count } = useCart()
  const navigate = useNavigate()

  if (items.length === 0) {
    return (
      <div className="container page center">
        <h1>Seu carrinho está vazio</h1>
        <p className="muted">Que tal dar uma olhada nos nossos instrumentos?</p>
        <Link to="/produtos" className="btn btn-primary">Ver produtos</Link>
      </div>
    )
  }

  return (
    <div className="container page">
      <h1>Carrinho</h1>
      <div className="cart">
        <ul className="cart-list">
          {items.map((i) => (
            <li key={i.id} className="cart-item">
              <Link to={`/produto/${i.id}`} className="cart-thumb"><ProductImage p={{ ...i, category: { kind: i.kind } }} /></Link>
              <div className="cart-info">
                <Link to={`/produto/${i.id}`} className="pcard-name">{i.name}</Link>
                <span className="muted small">{money(i.price)} cada</span>
                <button className="link-btn danger" onClick={() => remove(i.id)}>Remover</button>
              </div>
              <div className="qty" role="group" aria-label={`Quantidade de ${i.name}`}>
                <button onClick={() => setQty(i.id, i.quantity - 1)} aria-label="Diminuir">−</button>
                <span>{i.quantity}</span>
                <button onClick={() => setQty(i.id, i.quantity + 1)} disabled={i.quantity >= i.stock} aria-label="Aumentar">+</button>
              </div>
              <strong className="price">{money(i.price * i.quantity)}</strong>
            </li>
          ))}
        </ul>
        <aside className="summary">
          <h3>Resumo</h3>
          <div className="line"><span>Itens ({count})</span><span>{money(subtotal)}</span></div>
          <div className="line"><span>Frete</span><span>Grátis (demo)</span></div>
          <div className="line total"><span>Total</span><strong>{money(subtotal)}</strong></div>
          <button className="btn btn-primary block" onClick={() => navigate('/checkout')}>Finalizar compra</button>
          <Link to="/produtos" className="link center-text">Continuar comprando</Link>
        </aside>
      </div>
    </div>
  )
}
