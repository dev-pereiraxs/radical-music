"""Teste automático da API. Não precisa de MySQL: usa um SQLite temporário.

Uso (dentro da pasta backend):  python test_api.py
"""
import os, sys, tempfile
DB = os.path.join(tempfile.gettempdir(), 'rm_test.db')
if os.path.exists(DB):
    os.remove(DB)
os.environ.update(DB_ENGINE='sqlite', DB_NAME=DB, SECRET_KEY='t', FRONTEND_URL='http://localhost:5173')
sys.path.insert(0, '.')
import init_db; init_db.main()
import config, payments
from app import app
c = app.test_client()
ok = 0
def check(cond, msg):
    global ok
    if not cond: print('FALHOU:', msg); sys.exit(1)
    ok += 1
def J(r): return r.get_json()
def auth(t): return {'Authorization': 'Bearer ' + t}

check(J(c.get('/api/health'))['payment_mode'] == 'simulated', 'health')
f = J(c.get('/api/filters'))
check(len(f['categories']) == 8 and 'Ibanez' in f['brands'] and f['price_min'] == 19.9, 'filters')
r = J(c.get('/api/products'))
check(r['total'] == 24 and len(r['items']) == 12 and r['pages'] == 2, 'paginação')
check(J(c.get('/api/products?search=guitarra'))['total'] >= 4, 'busca')
check(J(c.get('/api/products?category=baixos'))['total'] == 2, 'categoria')
check(J(c.get('/api/products?brand=Ibanez'))['total'] == 2, 'marca')
check(all(p['price'] <= 100 for p in J(c.get('/api/products?max_price=100'))['items']), 'preço máx')
s = J(c.get('/api/products?sort=price_desc&per_page=3'))['items']
check(s[0]['price'] >= s[1]['price'] >= s[2]['price'], 'ordenação')
check(J(c.get('/api/products?featured=1'))['total'] == 7, 'destaques')
check(J(c.get('/api/products?search=violão'))['total'] >= 3, 'busca com acento')
check(c.get('/api/products/9999').status_code == 404, '404 produto')
check(J(c.get('/api/products/1'))['category']['kind'] == 'violao', 'detalhe')

# cadastro / login
r = c.post('/api/auth/register', json={'name': 'Maria', 'email': 'Maria@x.com', 'password': '123456'})
check(r.status_code == 201, 'register'); tok = J(r)['token']
check(c.post('/api/auth/register', json={'name': 'M', 'email': 'maria@x.com', 'password': '123456'}).status_code == 400, 'nome curto')
check(c.post('/api/auth/register', json={'name': 'Maria', 'email': 'maria@x.com', 'password': '123456'}).status_code == 409, 'duplicado')
check(c.post('/api/auth/register', json={'name': 'Maria', 'email': 'ruim', 'password': '123456'}).status_code == 400, 'email inválido')
check(c.post('/api/auth/login', json={'email': 'maria@x.com', 'password': 'errada'}).status_code == 401, 'senha errada')
r = c.post('/api/auth/login', json={'email': 'MARIA@x.com', 'password': '123456'}); check(r.status_code == 200, 'login')
check(J(c.get('/api/auth/me', headers=auth(tok)))['user']['email'] == 'maria@x.com', 'me')
check(c.get('/api/auth/me').status_code == 401, 'me sem token')
check(c.get('/api/auth/me', headers=auth('lixo')).status_code == 401, 'token inválido')

ship = {'name': 'Maria', 'zip': '01001-000', 'street': 'Rua A', 'number': '10', 'city': 'São Paulo', 'state': 'sp'}
def stock(pid): return J(c.get(f'/api/products/{pid}'))['stock']
check(c.post('/api/orders', json={'items': [{'product_id': 1, 'quantity': 1}], 'shipping': ship}).status_code == 401, 'pedido sem login')
check(c.post('/api/orders', headers=auth(tok), json={'items': [], 'shipping': ship}).status_code == 400, 'carrinho vazio')
check(c.post('/api/orders', headers=auth(tok), json={'items': [{'product_id': 1, 'quantity': 1}], 'shipping': {**ship, 'zip': '123'}}).status_code == 400, 'cep inválido')
s1, s4 = stock(1), stock(4)
# estoque insuficiente não deve baixar nada (rollback)
r = c.post('/api/orders', headers=auth(tok), json={'items': [{'product_id': 1, 'quantity': 2}, {'product_id': 4, 'quantity': 90}], 'shipping': ship})
check(r.status_code == 409 and stock(1) == s1 and stock(4) == s4, 'rollback estoque')
r = c.post('/api/orders', headers=auth(tok), json={'items': [{'product_id': 1, 'quantity': 2}, {'product_id': 1, 'quantity': 1}, {'product_id': 19, 'quantity': 3}], 'shipping': ship})
check(r.status_code == 201, 'criar pedido'); o = J(r)
check(o['status'] == 'pending_payment' and abs(o['total'] - (1899.90 * 3 + 129.90 * 3)) < 0.01, f"total {o['total']}")
check(o['shipping']['state'] == 'SP' and o['shipping']['zip'] == '01001000' and len(o['items']) == 2, 'dados do pedido')
check(stock(1) == s1 - 3, 'baixa de estoque')

# outro usuário não vê o pedido
t2 = J(c.post('/api/auth/register', json={'name': 'João', 'email': 'joao@x.com', 'password': 'abcdef'}))['token']
check(c.get(f"/api/orders/{o['id']}", headers=auth(t2)).status_code == 404, 'isolamento')

# pagamento simulado
p = J(c.post(f"/api/orders/{o['id']}/pay", headers=auth(tok)))
check(p['mode'] == 'simulated' and p['checkout_url'].endswith(f"/pagamento/{o['id']}"), 'start simulado')
r = J(c.post('/api/payments/simulate', headers=auth(tok), json={'order_id': o['id'], 'card_number': '4000 0000 0000 0002'}))
check(r['status'] == 'rejected', 'cartão recusado')
check(c.post('/api/payments/simulate', headers=auth(tok), json={'order_id': o['id'], 'card_number': '12'}).status_code == 400, 'cartão inválido')
check(c.post('/api/payments/simulate', headers=auth(t2), json={'order_id': o['id'], 'card_number': '4111111111111111'}).status_code == 404, 'simular pedido alheio')
r = J(c.post('/api/payments/simulate', headers=auth(tok), json={'order_id': o['id'], 'card_number': '4111 1111 1111 1111'}))
check(r['status'] == 'paid', 'aprovado')
check(J(c.get(f"/api/orders/{o['id']}", headers=auth(tok)))['status'] == 'paid', 'status pago')
check(c.post(f"/api/orders/{o['id']}/pay", headers=auth(tok)).status_code == 409, 'pagar de novo')
check(c.post(f"/api/orders/{o['id']}/cancel", headers=auth(tok)).status_code == 409, 'cancelar pago')

# cancelar pedido pendente devolve estoque
r = J(c.post('/api/orders', headers=auth(tok), json={'items': [{'product_id': 4, 'quantity': 2}], 'shipping': ship}))
check(stock(4) == s4 - 2, 'baixa 2'); 
check(J(c.post(f"/api/orders/{r['id']}/cancel", headers=auth(tok)))['status'] == 'cancelled' and stock(4) == s4, 'cancelar devolve estoque')
check(len(J(c.get('/api/orders', headers=auth(tok)))) == 2, 'meus pedidos')

# admin
check(c.get('/api/admin/summary', headers=auth(tok)).status_code == 403, 'cliente não é admin')
check(c.get('/api/admin/summary').status_code == 401, 'admin sem login')
at = J(c.post('/api/auth/login', json={'email': 'admin@radicalmusic.com', 'password': 'admin123'}))['token']
sm = J(c.get('/api/admin/summary', headers=auth(at)))
check(sm['orders'] == 2 and sm['customers'] == 2 and abs(sm['revenue'] - o['total']) < 0.01 and sm['pending'] == 0, f'summary {sm}')
check(any(x['stock'] <= 3 for x in sm['low_stock']), 'estoque baixo')
check(len(J(c.get('/api/admin/products', headers=auth(at)))) == 24, 'admin lista')
newp = {'name': 'Pedal Overdrive', 'brand': 'Radical', 'price': '199,90', 'stock': 5, 'category_id': 7, 'featured': True}
r = c.post('/api/admin/products', headers=auth(at), json=newp); check(r.status_code == 201, 'criar produto'); pid = J(r)['id']
check(J(r)['price'] == 199.9 and J(r)['category']['slug'] == 'acessorios', 'produto criado ok')
check(c.post('/api/admin/products', headers=auth(at), json={**newp, 'price': 'abc'}).status_code == 400, 'preço inválido')
check(c.post('/api/admin/products', headers=auth(at), json={**newp, 'category_id': 99}).status_code == 400, 'categoria inválida')
check(J(c.put(f'/api/admin/products/{pid}', headers=auth(at), json={**newp, 'name': 'Pedal Overdrive X', 'active': False}))['active'] is False, 'editar')
check(c.get(f'/api/products/{pid}').status_code == 404, 'inativo some da loja')
check(J(c.patch(f'/api/admin/products/{pid}/stock', headers=auth(at), json={'stock': 11}))['stock'] == 11, 'estoque')
check(c.patch(f'/api/admin/products/{pid}/stock', headers=auth(at), json={'stock': -1}).status_code == 400, 'estoque negativo')
check(J(c.delete(f'/api/admin/products/{pid}', headers=auth(at)))['deleted'] is True, 'excluir sem pedidos')
check(J(c.delete('/api/admin/products/1', headers=auth(at)))['deleted'] is False, 'desativar com pedidos')
orders = J(c.get('/api/admin/orders', headers=auth(at)))
check(len(orders) == 2 and orders[0]['customer']['name'] == 'Maria' and len(orders[1]['items']) == 2, 'admin pedidos')
check(len(J(c.get('/api/admin/orders?status=paid', headers=auth(at)))) == 1, 'filtro status')
check(c.patch(f"/api/admin/orders/{o['id']}/status", headers=auth(at), json={'status': 'shipped'}).status_code == 200, 'enviar')
s19 = stock(19)
check(c.patch(f"/api/admin/orders/{o['id']}/status", headers=auth(at), json={'status': 'cancelled'}).status_code == 200 and stock(19) == s19 + 3, 'cancelar admin devolve estoque')
check(c.patch(f"/api/admin/orders/{o['id']}/status", headers=auth(at), json={'status': 'paid'}).status_code == 409, 'não reabre')
check(c.patch(f"/api/admin/orders/{o['id']}/status", headers=auth(at), json={'status': 'xyz'}).status_code == 400, 'status inválido')

# Mercado Pago (com respostas falsas)
class Resp:
    def __init__(self, code, data): self.status_code, self._d = code, data
    def json(self): return self._d
config.MP_ACCESS_TOKEN = 'TEST-123'
calls = {}
def fake_post(url, json=None, headers=None, timeout=None):
    calls['post'] = (url, json, headers); return Resp(201, {'id': 'pref1', 'init_point': 'https://mp.test/checkout?pref=pref1'})
payments.requests.post = fake_post
r = J(c.post('/api/orders', headers=auth(tok), json={'items': [{'product_id': 19, 'quantity': 1}], 'shipping': ship}))
pay = J(c.post(f"/api/orders/{r['id']}/pay", headers=auth(tok)))
body = calls['post'][1]
check(pay == {'mode': 'mercadopago', 'checkout_url': 'https://mp.test/checkout?pref=pref1'}, 'preferência MP')
check(body['external_reference'] == str(r['id']) and body['items'][0]['unit_price'] == 129.9 and body['items'][0]['currency_id'] == 'BRL', 'corpo MP')
check(calls['post'][2]['Authorization'] == 'Bearer TEST-123' and body['back_urls']['success'].endswith(f"/pedido/{r['id']}"), 'headers/back_urls')
check(c.post('/api/payments/simulate', headers=auth(tok), json={'order_id': r['id'], 'card_number': '4111111111111111'}).status_code == 404, 'simulado desligado com MP')
state = {'status': 'pending', 'ref': str(r['id'])}
payments.requests.get = lambda url, headers=None, timeout=None: Resp(200, {'status': state['status'], 'external_reference': state['ref']})
conf = lambda pid='555': J(c.post(f"/api/orders/{r['id']}/confirm-payment", headers=auth(tok), json={'payment_id': pid}))
check(conf()['result'] == 'pending', 'pendente')
state['status'] = 'rejected'; check(conf()['result'] == 'rejected', 'rejeitado')
check(c.post(f"/api/orders/{r['id']}/confirm-payment", headers=auth(tok), json={'payment_id': 'abc'}).status_code == 400, 'id inválido')
state['ref'] = '99999'; state['status'] = 'approved'
check(c.post(f"/api/orders/{r['id']}/confirm-payment", headers=auth(tok), json={'payment_id': '555'}).status_code == 400, 'pagamento de outro pedido')
state['ref'] = str(r['id'])
x = conf(); check(x['result'] == 'paid' and x['order']['status'] == 'paid' and x['order']['payment_provider'] == 'mercadopago', 'aprovado MP')
# webhook
r2 = J(c.post('/api/orders', headers=auth(tok), json={'items': [{'product_id': 21, 'quantity': 1}], 'shipping': ship}))
state['ref'] = str(r2['id'])
check(c.post('/api/payments/webhook', json={'type': 'payment', 'data': {'id': '777'}}).status_code == 200, 'webhook')
check(J(c.get(f"/api/orders/{r2['id']}", headers=auth(tok)))['status'] == 'paid', 'webhook marcou pago')
check(c.get('/api/nao-existe').status_code == 404 and 'error' in J(c.get('/api/nao-existe')), '404 json')
check(c.options('/api/products').headers.get('Access-Control-Allow-Origin') == 'http://localhost:5173', 'cors')
print(f'OK: {ok} verificações passaram')
