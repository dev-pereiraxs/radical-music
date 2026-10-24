<<<<<<< HEAD
# radical-music
=======
# Radical Music — loja virtual de instrumentos musicais

Loja virtual completa de **violões, guitarras, baixos, baterias, teclados e acessórios** (cordas, palhetas, capotrastes, suportes), com cadastro e login, catálogo com busca e filtros, carrinho, pedidos, painel administrativo de estoque e pagamento em ambiente de teste.

> Projeto de portfólio. A loja é fictícia: produtos e preços são exemplos e nenhuma cobrança real é feita.

| Parte | Tecnologia |
| --- | --- |
| Interface | React 18 + Vite (JavaScript) |
| API | Python + Flask |
| Banco de dados | MySQL (XAMPP, no desenvolvimento) |
| Pagamento | Mercado Pago (ambiente de teste) ou pagamento simulado |
| Ferramentas | Node.js (roda o Vite/React), Python 3.10+ |

Visual: tema claro em branco e azul (degradê de claro para escuro) e a mesma pilha de fontes do Instagram na web (fontes do sistema).

## Funcionalidades

- **Contas:** cadastro, login (token JWT) e área "Meus pedidos".
- **Catálogo:** busca por texto, filtro por categoria, marca, faixa de preço e "apenas em estoque", ordenação e paginação.
- **Carrinho** que fica salvo no navegador, **checkout** com endereço de entrega e **pedidos** com status.
- **Estoque seguro:** a baixa é feita na criação do pedido, de forma atômica. Se o pedido for cancelado, o estoque volta.
- **Painel administrativo** (`/admin`): resumo de vendas, alerta de estoque baixo, cadastro/edição/exclusão de produtos, ajuste rápido de estoque e gestão do status dos pedidos.
- **Pagamento em teste:** Mercado Pago (Checkout Pro) ou, sem configurar nada, um pagamento simulado.

## Estrutura

```
radical-music/
├── backend/                 API Flask
│   ├── app.py               aplicação e rotas registradas
│   ├── routes_auth.py       cadastro, login, perfil
│   ├── routes_catalog.py    produtos, busca e filtros
│   ├── routes_orders.py     pedidos, cancelamento, pagamento
│   ├── routes_admin.py      painel administrativo
│   ├── payments.py          Mercado Pago, webhook e pagamento simulado
│   ├── services.py, auth.py, db.py, config.py
│   ├── schema.sql           tabelas do MySQL
│   ├── init_db.py           cria banco, tabelas e dados de exemplo
│   ├── test_api.py          teste automático da API (não precisa de MySQL)
│   ├── requirements.txt
│   └── .env.example
└── frontend/                site em React
    ├── public/              logo e fotos dos produtos
    └── src/ (pages, components, context, styles.css)
```

## Como rodar no VSCode (Windows)

Você precisa de: **Node.js 18+**, **Python 3.10+** e o **XAMPP**.

**1. Ligue o MySQL.** Abra o XAMPP e clique em **Start** no módulo **MySQL**.

**2. Back-end** (terminal do VSCode, na pasta `radical-music`):

```powershell
cd backend
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python init_db.py
python app.py
```

O `init_db.py` cria o banco `radical_music`, as tabelas, 24 produtos de exemplo e a conta de administrador. A API fica em `http://localhost:5000`. Deixe este terminal aberto.

**3. Front-end** (um segundo terminal, também na pasta `radical-music`):

```powershell
cd frontend
npm install
npm run dev
```

Abra **http://localhost:5173**.

Se o seu MySQL tiver senha ou outra porta, ajuste `DB_PASSWORD` e `DB_PORT` no arquivo `backend/.env`.

## Contas

- **Administrador:** `admin@radicalmusic.com` / `admin123` (definidos no `.env`; **troque antes de publicar**).
- **Cliente:** crie a sua pelo botão "Entrar" → "Criar conta".

## Pagamento em ambiente de teste

**Modo simulado (padrão).** Com `MP_ACCESS_TOKEN` vazio no `.env`, o checkout leva a uma tela de cartão de teste dentro do próprio site. O cartão `4111 1111 1111 1111` aprova e `4000 0000 0000 0002` recusa. Nenhum dado de cartão é guardado.

**Mercado Pago (teste).**
1. Crie uma conta em *mercadopago.com.br/developers* e uma aplicação.
2. Copie as **credenciais de teste** e cole o *Access Token* em `MP_ACCESS_TOKEN` no `backend/.env`. Reinicie o `python app.py`.
3. No checkout, o cliente é enviado ao Mercado Pago. Ao voltar para a loja, o site confere o pagamento direto na API do Mercado Pago e atualiza o pedido.
4. Use os **cartões e usuários de teste** da documentação do Mercado Pago (eles mudam com o tempo, então consulte a lista atual lá).

Se quiser que o Mercado Pago avise a loja automaticamente, publique o back-end e preencha `MP_NOTIFICATION_URL` com `https://SEU-SERVIDOR/api/payments/webhook`. Localmente isso não é necessário.

## Fotos dos produtos

As fotos ficam em `frontend/public/products/`. Produtos sem foto mostram uma ilustração. Para usar uma foto, salve-a nessa pasta e, no painel admin, edite o produto preenchendo **Imagem** com o caminho, por exemplo `/products/minha-foto.webp`.

## API (resumo)

| Rota | O que faz |
| --- | --- |
| `POST /api/auth/register`, `/login`, `GET /api/auth/me` | conta e sessão |
| `GET /api/filters`, `/api/products`, `/api/products/<id>` | catálogo, busca e filtros |
| `POST /api/orders`, `GET /api/orders`, `/api/orders/<id>` | pedidos do usuário |
| `POST /api/orders/<id>/pay`, `/confirm-payment`, `/cancel` | pagamento e cancelamento |
| `POST /api/payments/simulate`, `/webhook` | pagamento simulado e aviso do Mercado Pago |
| `/api/admin/...` | resumo, produtos, estoque e pedidos (só administrador) |

## Testes

```powershell
cd backend
python test_api.py
```

Roda 75 verificações da API (cadastro, filtros, estoque, pedidos, pagamento e painel admin) usando um banco temporário, sem precisar do MySQL.

## Publicação gratuita (um link só)

O site e a API ficam juntos em um único serviço do **Render** (o Flask entrega o site compilado), o banco fica no **Aiven** (MySQL gratuito) e o código fica no **GitHub**. Os planos gratuitos mudam, então confira os limites atuais em cada site.

1. **Banco (Aiven):** crie uma conta em aiven.io, crie um serviço **MySQL** no plano **Free** e anote host, porta, usuário, senha e nome do banco (`defaultdb`).
2. **Crie as tabelas nele:** no `backend/.env` local, coloque esses dados em `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` e `DB_SSL=true`, e rode `python init_db.py`. Depois volte o `.env` para o XAMPP (ou guarde uma cópia).
3. **Compile o site e copie para o back-end:**
   ```powershell
   cd frontend
   npm run build
   Remove-Item -Recurse -Force ..\backend\site -ErrorAction SilentlyContinue
   Copy-Item -Recurse dist ..\backend\site
   ```
4. **GitHub:** envie a pasta do projeto (que tem `backend` e `frontend`) para um repositório. O `.env` não vai junto, porque está no `.gitignore`.
5. **Render:** em render.com, **New → Web Service**, escolha o repositório e configure:
   - *Root Directory:* `backend`
   - *Build Command:* `pip install -r requirements.txt`
   - *Start Command:* `gunicorn app:app`
   - *Instance Type:* Free
   - *Environment:* `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_SSL=true`, `SECRET_KEY` (texto longo e aleatório), `ADMIN_EMAIL`, `ADMIN_PASSWORD` e `FRONTEND_URL` (o endereço que o Render mostrar, sem barra no final).
6. O link da loja é o endereço do serviço, algo como `https://radical-music.onrender.com`.

Para atualizar a loja: refaça o passo 3 quando mudar o front-end e envie com `git push`; o Render publica sozinho.

No plano gratuito, o Render "dorme" após 15 minutos sem visitas e a primeira visita seguinte leva cerca de 1 minuto. O Aiven pode desligar o banco se ficar sem uso por muito tempo (ele avisa antes e você religa pelo painel).

## Cuidados e limitações

- É um projeto de demonstração: não há limite de tentativas de login, recuperação de senha nem envio de e-mails.
- Troque `SECRET_KEY` e a senha do administrador antes de publicar, e use HTTPS.
- O frete é fixo ("Grátis (demo)") e o endereço não consulta CEP.
- O pagamento só funciona em ambiente de teste.

## Problemas comuns

- **"Não foi possível conectar ao servidor":** o `python app.py` não está rodando ou o venv não está ativo.
- **"Can't connect to MySQL" / "Access denied":** o MySQL do XAMPP não está ligado ou o `.env` está com usuário/senha diferentes.
- **Porta 5000 ocupada (macOS):** rode a API em outra porta e ajuste `proxy` em `frontend/vite.config.js`.
- **Erro ao ativar o venv no PowerShell:** rode antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`.
>>>>>>> eca7607 (Radical Music)
