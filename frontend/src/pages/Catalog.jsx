import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api.js'
import ProductCard from '../components/ProductCard.jsx'

const PARAMS = { busca: 'search', categoria: 'category', marca: 'brand', min: 'min_price', max: 'max_price', estoque: 'in_stock', ordem: 'sort', pagina: 'page' }

export default function Catalog() {
  const [sp, setSp] = useSearchParams()
  const [filters, setFilters] = useState({ categories: [], brands: [] })
  const [data, setData] = useState({ items: [], total: 0, page: 1, pages: 1 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const get = (k) => sp.get(k) || ''

  useEffect(() => {
    api('/filters', { auth: false }).then(setFilters).catch(() => {})
  }, [])

  useEffect(() => {
    const q = new URLSearchParams({ per_page: '12' })
    for (const [k, apiKey] of Object.entries(PARAMS)) if (sp.get(k)) q.set(apiKey, sp.get(k))
    setLoading(true)
    setError('')
    api(`/products?${q}`, { auth: false })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [sp])

  const update = (changes) => {
    const next = new URLSearchParams(sp)
    for (const [k, v] of Object.entries(changes)) {
      if (v === '' || v == null || v === false) next.delete(k)
      else next.set(k, v === true ? '1' : v)
    }
    if (!('pagina' in changes)) next.delete('pagina')
    setSp(next)
  }

  const applyPrice = (e) => {
    e.preventDefault()
    const f = e.currentTarget.elements
    update({ min: f.min.value.trim(), max: f.max.value.trim() })
  }

  const active = ['busca', 'categoria', 'marca', 'min', 'max', 'estoque'].some((k) => get(k))
  const title = get('busca') ? `Resultados para "${get('busca')}"` : filters.categories.find((c) => c.slug === get('categoria'))?.name || 'Todos os produtos'

  return (
    <div className="container page">
      <h1>{title}</h1>
      <div className="catalog">
        <aside className="filters" aria-label="Filtros">
          <h3>Categoria</h3>
          <button className={!get('categoria') ? 'opt on' : 'opt'} onClick={() => update({ categoria: '' })}>Todas</button>
          {filters.categories.map((c) => (
            <button key={c.id} className={get('categoria') === c.slug ? 'opt on' : 'opt'} onClick={() => update({ categoria: c.slug })}>
              {c.name} <span className="muted">({c.count})</span>
            </button>
          ))}

          <h3>Marca</h3>
          <select value={get('marca')} onChange={(e) => update({ marca: e.target.value })} aria-label="Marca">
            <option value="">Todas as marcas</option>
            {filters.brands.map((b) => <option key={b} value={b}>{b}</option>)}
          </select>

          <h3>Preço (R$)</h3>
          <form key={`${get('min')}-${get('max')}`} onSubmit={applyPrice} className="price-form">
            <input name="min" inputMode="decimal" placeholder="Mín." defaultValue={get('min')} aria-label="Preço mínimo" />
            <input name="max" inputMode="decimal" placeholder="Máx." defaultValue={get('max')} aria-label="Preço máximo" />
            <button className="btn btn-ghost btn-sm" type="submit">Aplicar</button>
          </form>

          <label className="check">
            <input type="checkbox" checked={get('estoque') === '1'} onChange={(e) => update({ estoque: e.target.checked })} />
            Apenas em estoque
          </label>
          {active && <button className="link-btn" onClick={() => setSp(new URLSearchParams())}>Limpar filtros</button>}
        </aside>

        <section>
          <div className="toolbar">
            <span className="muted">{loading ? 'Carregando…' : `${data.total} produto${data.total === 1 ? '' : 's'}`}</span>
            <label>
              Ordenar por{' '}
              <select value={get('ordem')} onChange={(e) => update({ ordem: e.target.value })}>
                <option value="">Destaques</option>
                <option value="price_asc">Menor preço</option>
                <option value="price_desc">Maior preço</option>
                <option value="name">Nome (A–Z)</option>
                <option value="newest">Mais recentes</option>
              </select>
            </label>
          </div>
          {error && <p className="alert alert-bad">{error}</p>}
          {!loading && !error && data.items.length === 0 && (
            <div className="empty"><h3>Nada encontrado</h3><p className="muted">Tente outra busca ou remova alguns filtros.</p></div>
          )}
          <div className="grid">{data.items.map((p) => <ProductCard key={p.id} p={p} />)}</div>
          {data.pages > 1 && (
            <div className="pager">
              <button className="btn btn-ghost btn-sm" disabled={data.page <= 1} onClick={() => update({ pagina: String(data.page - 1) })}>← Anterior</button>
              <span>Página {data.page} de {data.pages}</span>
              <button className="btn btn-ghost btn-sm" disabled={data.page >= data.pages} onClick={() => update({ pagina: String(data.page + 1) })}>Próxima →</button>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
