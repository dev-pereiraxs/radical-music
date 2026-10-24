// Ilustração usada quando o produto não tem foto. Para usar uma foto, preencha o campo "image" no painel admin.
const Defs = () => (
  <defs>
    <linearGradient id="pa-g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stopColor="#6fb4ff" />
      <stop offset="1" stopColor="#0b3a8a" />
    </linearGradient>
  </defs>
)

const ART = {
  guitarra: (
    <g transform="rotate(35 100 100)">
      <rect x="95" y="14" width="10" height="92" rx="2" fill="#0b2f6b" />
      <rect x="91" y="4" width="18" height="18" rx="4" fill="#1556b0" />
      <ellipse cx="100" cy="132" rx="30" ry="34" fill="url(#pa-g)" />
      <ellipse cx="100" cy="106" rx="21" ry="21" fill="url(#pa-g)" />
      <circle cx="100" cy="126" r="7" fill="#0b2f6b" />
    </g>
  ),
  baixo: (
    <g transform="rotate(35 100 100)">
      <rect x="96" y="2" width="8" height="112" rx="2" fill="#0b2f6b" />
      <rect x="92" y="-4" width="16" height="14" rx="3" fill="#1556b0" />
      <ellipse cx="100" cy="140" rx="24" ry="30" fill="url(#pa-g)" />
      <rect x="90" y="132" width="20" height="5" rx="2" fill="#0b2f6b" />
      <rect x="90" y="146" width="20" height="5" rx="2" fill="#0b2f6b" />
    </g>
  ),
  bateria: (
    <g>
      <ellipse cx="100" cy="132" rx="46" ry="42" fill="url(#pa-g)" />
      <ellipse cx="100" cy="132" rx="30" ry="27" fill="#e1efff" />
      <ellipse cx="58" cy="92" rx="22" ry="9" fill="#1556b0" /><rect x="36" y="92" width="44" height="22" fill="#2f80ed" />
      <ellipse cx="142" cy="92" rx="22" ry="9" fill="#1556b0" /><rect x="120" y="92" width="44" height="22" fill="#2f80ed" />
      <ellipse cx="38" cy="52" rx="28" ry="5" fill="#7fb6f5" /><rect x="37" y="52" width="2" height="44" fill="#0b2f6b" />
      <ellipse cx="164" cy="48" rx="28" ry="5" fill="#7fb6f5" /><rect x="163" y="48" width="2" height="48" fill="#0b2f6b" />
    </g>
  ),
  teclado: (
    <g>
      <rect x="12" y="62" width="176" height="80" rx="8" fill="url(#pa-g)" />
      <rect x="22" y="86" width="156" height="48" rx="3" fill="#fff" />
      {Array.from({ length: 12 }, (_, i) => <rect key={i} x={22 + i * 13} y="86" width="1.4" height="48" fill="#b9d3f2" />)}
      {[1, 2, 4, 5, 6, 8, 9, 11].map((k) => <rect key={k} x={22 + k * 13 - 4} y="86" width="8" height="28" rx="1.5" fill="#0b2f6b" />)}
      <circle cx="34" cy="74" r="4" fill="#bcdcff" /><circle cx="50" cy="74" r="4" fill="#bcdcff" />
    </g>
  ),
  cordas: (
    <g>
      <rect x="40" y="34" width="120" height="132" rx="10" fill="url(#pa-g)" />
      <rect x="54" y="48" width="92" height="30" rx="5" fill="#e1efff" />
      {[0, 1, 2, 3, 4, 5].map((i) => <rect key={i} x={62 + i * 15} y="86" width="2.2" height="66" fill="#d7e8ff" />)}
    </g>
  ),
  acessorios: (
    <g>
      <path d="M100 38c40 0 60 22 52 62-7 30-30 54-52 68-22-14-45-38-52-68-8-40 12-62 52-62z" fill="url(#pa-g)" />
      <path d="M100 56c26 0 40 15 35 42-5 22-20 40-35 51-15-11-30-29-35-51-5-27 9-42 35-42z" fill="none" stroke="#e1efff" strokeWidth="3" opacity=".75" />
      <rect x="150" y="30" width="34" height="14" rx="7" fill="#7fb6f5" transform="rotate(35 167 37)" />
    </g>
  ),
  amplificador: (
    <g>
      <rect x="36" y="30" width="128" height="140" rx="10" fill="url(#pa-g)" />
      <circle cx="100" cy="116" r="38" fill="#0b2f6b" /><circle cx="100" cy="116" r="22" fill="#2f80ed" /><circle cx="100" cy="116" r="7" fill="#0b2f6b" />
      {[60, 80, 100, 120].map((x) => <circle key={x} cx={x + 10} cy="50" r="5" fill="#e1efff" />)}
    </g>
  ),
}
ART.violao = ART.guitarra

export function ProductArt({ kind }) {
  return (
    <svg viewBox="0 0 200 200" className="art" role="img" aria-label="Ilustração do produto">
      <Defs />
      {ART[kind] || ART.acessorios}
    </svg>
  )
}

export function ProductImage({ p, eager = false }) {
  if (p.image) {
    return <img src={p.image} alt={p.name} loading={eager ? 'eager' : 'lazy'} />
  }
  return <ProductArt kind={p.category?.kind || p.kind} />
}
