import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import ProductCard from '../components/ProductCard.jsx'
import { ProductArt } from '../components/ProductArt.jsx'

export default function Home() {
  const [featured, setFeatured] = useState([])
  const [cats, setCats] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    api('/products?featured=1&per_page=8', { auth: false }).then((d) => setFeatured(d.items)).catch((e) => setError(e.message))
    api('/filters', { auth: false }).then((d) => setCats(d.categories)).catch(() => {})
  }, [])

  return (
    <>
      <section className="hero">
        <div className="container hero-inner">
          <div className="hero-text">
            <span className="pill">Instrumentos e acessórios</span>
            <h1>O som da sua banda começa aqui.</h1>
            <p>Violões, guitarras, baixos, baterias, teclados e tudo o que vai com eles: cordas, palhetas, capotrastes e suportes.</p>
            <div className="row">
              <Link to="/produtos" className="btn btn-primary">Ver produtos</Link>
              <Link to="/produtos?categoria=acessorios" className="btn btn-light">Acessórios</Link>
            </div>
          </div>
          <div className="hero-cards" aria-hidden="true">
            <div className="hcard c1"><img src="/products/ibanez-pf15ece.webp" alt="" /></div>
            <div className="hcard c2"><img src="/products/bc-rich-warlock.webp" alt="" /></div>
            <div className="hcard c3"><img src="/products/ibanez-sr-roxo.webp" alt="" /></div>
          </div>
        </div>
      </section>

      <section className="container section">
        <h2>Categorias</h2>
        <div className="cat-grid">
          {cats.map((c) => (
            <Link key={c.id} to={`/produtos?categoria=${c.slug}`} className="cat-card">
              <div className="cat-art"><ProductArt kind={c.kind} /></div>
              <strong>{c.name}</strong>
              <span className="muted small">{c.count} produtos</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="container section">
        <div className="section-head">
          <h2>Destaques</h2>
          <Link to="/produtos" className="link">Ver todos →</Link>
        </div>
        {error && <p className="alert alert-bad">{error}</p>}
        <div className="grid">{featured.map((p) => <ProductCard key={p.id} p={p} />)}</div>
      </section>
    </>
  )
}
