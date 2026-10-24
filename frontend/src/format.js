export const money = (v) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export const STATUS = {
  pending_payment: { label: 'Aguardando pagamento', tone: 'warn' },
  paid: { label: 'Pago', tone: 'ok' },
  shipped: { label: 'Enviado', tone: 'info' },
  delivered: { label: 'Entregue', tone: 'ok' },
  cancelled: { label: 'Cancelado', tone: 'bad' },
}

export const dateTime = (iso) => {
  if (!iso) return ''
  const d = new Date(String(iso).replace(' ', 'T'))
  return isNaN(d) ? '' : d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

export const cep = (z) => (z && z.length === 8 ? `${z.slice(0, 5)}-${z.slice(5)}` : z)
