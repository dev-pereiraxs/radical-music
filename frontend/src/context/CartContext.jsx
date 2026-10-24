import { createContext, useContext, useEffect, useState } from 'react'

const Ctx = createContext(null)
export const useCart = () => useContext(Ctx)
const KEY = 'rm_cart'

function load() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || []
  } catch {
    return []
  }
}

export function CartProvider({ children }) {
  const [items, setItems] = useState(load)

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(items))
  }, [items])

  const add = (p, qty = 1) =>
    setItems((cur) => {
      const max = Math.max(p.stock, 0)
      const found = cur.find((x) => x.id === p.id)
      if (found) {
        return cur.map((x) =>
          x.id === p.id ? { ...x, stock: p.stock, quantity: Math.min(x.quantity + qty, max) } : x,
        )
      }
      return [
        ...cur,
        { id: p.id, name: p.name, price: p.price, image: p.image, kind: p.category.kind, stock: p.stock, quantity: Math.min(qty, max) },
      ]
    })
  const setQty = (id, q) =>
    setItems((cur) => cur.map((x) => (x.id === id ? { ...x, quantity: Math.max(1, Math.min(q, x.stock)) } : x)))
  const remove = (id) => setItems((cur) => cur.filter((x) => x.id !== id))
  const clear = () => setItems([])

  const count = items.reduce((s, i) => s + i.quantity, 0)
  const subtotal = items.reduce((s, i) => s + i.price * i.quantity, 0)

  return <Ctx.Provider value={{ items, add, setQty, remove, clear, count, subtotal }}>{children}</Ctx.Provider>
}
