import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div>
          <img src="/logo.png" alt="Radical Music" className="footer-logo" />
        </div>
        <div>
          <h4>Loja</h4>
          <Link to="/produtos">Todos os produtos</Link>
          <Link to="/produtos?categoria=violoes">Violões</Link>
          <Link to="/produtos?categoria=guitarras">Guitarras</Link>
          <Link to="/produtos?categoria=acessorios">Acessórios</Link>
        </div>
        <div>
          <h4>Conta</h4>
          <Link to="/entrar">Entrar</Link>
          <Link to="/cadastro">Criar conta</Link>
          <Link to="/meus-pedidos">Meus pedidos</Link>
        </div>
        <div>
          <h4>Sobre este site</h4>
          <p className="small">
            Projeto de portfólio. A loja é fictícia: produtos e preços são exemplos e os pagamentos acontecem
            apenas em ambiente de teste, sem cobrança real.
          </p>
        </div>
      </div>
      <div className="footer-end">© {new Date().getFullYear()} Radical Music · Projeto de demonstração</div>
    </footer>
  )
}
