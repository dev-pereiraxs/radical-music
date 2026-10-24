import re

from flask import Blueprint, g, jsonify, request

import db
import payments
from auth import err, login_required
from services import cancel_and_restock, get_order

bp = Blueprint('orders', __name__, url_prefix='/api/orders')


def clean_shipping(s):
    fields = {k: str(s.get(k) or '').strip() for k in
              ('name', 'zip', 'street', 'number', 'complement', 'district', 'city', 'state')}
    fields['zip'] = re.sub(r'\D', '', fields['zip'])
    fields['state'] = fields['state'].upper()
    for key, label in (('name', 'nome'), ('street', 'rua'), ('number', 'número'), ('city', 'cidade')):
        if not fields[key]:
            return None, f'Informe o campo {label}.'
    if len(fields['zip']) != 8:
        return None, 'CEP inválido (use 8 números).'
    if len(fields['state']) != 2:
        return None, 'Informe o estado com 2 letras (ex.: SP).'
    limits = {'name': 120, 'street': 160, 'number': 20, 'complement': 80, 'district': 80, 'city': 80}
    for key, size in limits.items():
        fields[key] = fields[key][:size]
    return fields, None


def _mine(order_id):
    """Pedido do usuário logado (ou de qualquer um, se for admin)."""
    row = db.query('SELECT user_id FROM orders WHERE id=%s', (order_id,), one=True)
    if not row or (row['user_id'] != g.user['id'] and not g.user['is_admin']):
        return None
    return get_order(order_id)


@bp.post('')
@login_required
def create_order():
    d = request.get_json(silent=True) or {}
    raw = d.get('items')
    if not isinstance(raw, list) or not raw:
        return err('Seu carrinho está vazio.')
    wanted = {}
    for it in raw:
        try:
            pid, qty = int(it.get('product_id')), int(it.get('quantity'))
        except (TypeError, ValueError, AttributeError):
            return err('Item inválido no carrinho.')
        if qty < 1:
            return err('Quantidade inválida.')
        wanted[pid] = wanted.get(pid, 0) + qty
    if any(q > 99 for q in wanted.values()):
        return err('Quantidade máxima por produto: 99.')

    ship, problem = clean_shipping(d.get('shipping') or {})
    if problem:
        return err(problem)

    marks = ','.join(['%s'] * len(wanted))
    products = {p['id']: p for p in db.query(
        f'SELECT id, name, price, stock, active FROM products WHERE id IN ({marks})', list(wanted))}

    total = 0
    lines = []
    for pid, qty in wanted.items():
        p = products.get(pid)
        if not p or not p['active']:
            return err('Um dos produtos não está mais disponível.', 409)
        # Reserva o estoque de forma atômica: só baixa se ainda houver unidades.
        _, changed = db.execute(
            'UPDATE products SET stock = stock - %s WHERE id=%s AND stock >= %s AND active = 1',
            (qty, pid, qty))
        if not changed:
            db.rollback()
            return err(f"Estoque insuficiente para \"{p['name']}\".", 409)
        price = round(float(p['price']), 2)
        total += round(price * qty, 2)
        lines.append((pid, p['name'], price, qty))

    order_id, _ = db.execute(
        'INSERT INTO orders (user_id, status, total, ship_name, ship_zip, ship_street, ship_number, '
        'ship_complement, ship_district, ship_city, ship_state) '
        "VALUES (%s, 'pending_payment', %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (g.user['id'], f'{total:.2f}', ship['name'], ship['zip'], ship['street'], ship['number'],
         ship['complement'], ship['district'], ship['city'], ship['state']))
    for pid, name, price, qty in lines:
        db.execute('INSERT INTO order_items (order_id, product_id, name, unit_price, quantity) '
                   'VALUES (%s, %s, %s, %s, %s)', (order_id, pid, name, f'{price:.2f}', qty))
    db.commit()
    return jsonify(get_order(order_id)), 201


@bp.get('')
@login_required
def my_orders():
    ids = [r['id'] for r in db.query(
        'SELECT id FROM orders WHERE user_id=%s ORDER BY id DESC', (g.user['id'],))]
    return jsonify([get_order(i) for i in ids])


@bp.get('/<int:order_id>')
@login_required
def one_order(order_id):
    order = _mine(order_id)
    return jsonify(order) if order else err('Pedido não encontrado.', 404)


@bp.post('/<int:order_id>/cancel')
@login_required
def cancel(order_id):
    order = _mine(order_id)
    if not order:
        return err('Pedido não encontrado.', 404)
    if order['status'] != 'pending_payment':
        return err('Só é possível cancelar pedidos que aguardam pagamento.', 409)
    cancel_and_restock(order_id)
    return jsonify(get_order(order_id))


@bp.post('/<int:order_id>/pay')
@login_required
def pay(order_id):
    order = _mine(order_id)
    if not order:
        return err('Pedido não encontrado.', 404)
    if order['status'] != 'pending_payment':
        return err('Este pedido não está aguardando pagamento.', 409)
    try:
        return jsonify(payments.start_checkout(order))
    except payments.PaymentError as e:
        return err(str(e), 502)


@bp.post('/<int:order_id>/confirm-payment')
@login_required
def confirm(order_id):
    order = _mine(order_id)
    if not order:
        return err('Pedido não encontrado.', 404)
    if order['status'] != 'pending_payment':
        return jsonify({'result': 'paid' if order['status'] != 'cancelled' else 'cancelled', 'order': order})
    payment_id = (request.get_json(silent=True) or {}).get('payment_id')
    try:
        result = payments.confirm_payment(order, payment_id)
    except payments.PaymentError as e:
        return err(str(e), 400)
    return jsonify({'result': result, 'order': get_order(order_id)})
