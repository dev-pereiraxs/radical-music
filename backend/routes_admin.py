from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

import db
from auth import admin_required, err
from routes_catalog import SELECT
from services import STATUSES, cancel_and_restock, format_order, product_to_dict

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def parse_product(d):
    name = str(d.get('name') or '').strip()
    if len(name) < 3:
        return None, 'Informe o nome do produto.'
    try:
        price = Decimal(str(d.get('price')).replace(',', '.')).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return None, 'Preço inválido.'
    if price <= 0 or price > Decimal('999999'):
        return None, 'Preço inválido.'
    try:
        stock = int(d.get('stock'))
        category_id = int(d.get('category_id'))
    except (TypeError, ValueError):
        return None, 'Estoque e categoria são obrigatórios.'
    if stock < 0:
        return None, 'O estoque não pode ser negativo.'
    if not db.query('SELECT id FROM categories WHERE id=%s', (category_id,), one=True):
        return None, 'Categoria inexistente.'
    return {
        'name': name[:160], 'brand': str(d.get('brand') or '').strip()[:60] or None,
        'description': str(d.get('description') or '').strip() or None,
        'price': f'{price:.2f}', 'stock': stock, 'category_id': category_id,
        'image': str(d.get('image') or '').strip()[:255] or None,
        'featured': 1 if d.get('featured') else 0, 'active': 0 if d.get('active') is False else 1,
    }, None


@bp.get('/summary')
@admin_required
def summary():
    one = lambda sql: db.query(sql, one=True)['n']
    return jsonify({
        'products': one('SELECT COUNT(*) AS n FROM products WHERE active=1'),
        'customers': one('SELECT COUNT(*) AS n FROM users WHERE is_admin=0'),
        'orders': one('SELECT COUNT(*) AS n FROM orders'),
        'pending': one("SELECT COUNT(*) AS n FROM orders WHERE status='pending_payment'"),
        'revenue': float(db.query(
            "SELECT COALESCE(SUM(total), 0) AS n FROM orders WHERE status IN ('paid','shipped','delivered')",
            one=True)['n']),
        'low_stock': db.query('SELECT id, name, stock FROM products WHERE active=1 AND stock <= 3 '
                              'ORDER BY stock, id LIMIT 6'),
    })


@bp.get('/products')
@admin_required
def list_products():
    search = (request.args.get('search') or '').strip()
    where, params = '', []
    if search:
        where, params = ' WHERE p.name LIKE %s OR p.brand LIKE %s', [f'%{search}%'] * 2
    rows = db.query(f'{SELECT}{where} ORDER BY p.id DESC LIMIT 300', params)
    return jsonify([product_to_dict(r) for r in rows])


@bp.post('/products')
@admin_required
def create_product():
    f, problem = parse_product(request.get_json(silent=True) or {})
    if problem:
        return err(problem)
    pid, _ = db.execute(
        'INSERT INTO products (category_id, name, brand, description, price, stock, image, featured, active) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (f['category_id'], f['name'], f['brand'], f['description'], f['price'], f['stock'],
         f['image'], f['featured'], f['active']))
    db.commit()
    return jsonify(product_to_dict(db.query(f'{SELECT} WHERE p.id=%s', (pid,), one=True))), 201


@bp.put('/products/<int:pid>')
@admin_required
def update_product(pid):
    if not db.query('SELECT id FROM products WHERE id=%s', (pid,), one=True):
        return err('Produto não encontrado.', 404)
    f, problem = parse_product(request.get_json(silent=True) or {})
    if problem:
        return err(problem)
    db.execute(
        'UPDATE products SET category_id=%s, name=%s, brand=%s, description=%s, price=%s, stock=%s, '
        'image=%s, featured=%s, active=%s WHERE id=%s',
        (f['category_id'], f['name'], f['brand'], f['description'], f['price'], f['stock'],
         f['image'], f['featured'], f['active'], pid))
    db.commit()
    return jsonify(product_to_dict(db.query(f'{SELECT} WHERE p.id=%s', (pid,), one=True)))


@bp.patch('/products/<int:pid>/stock')
@admin_required
def set_stock(pid):
    try:
        stock = int((request.get_json(silent=True) or {}).get('stock'))
    except (TypeError, ValueError):
        return err('Estoque inválido.')
    if stock < 0:
        return err('O estoque não pode ser negativo.')
    _, changed = db.execute('UPDATE products SET stock=%s WHERE id=%s', (stock, pid))
    db.commit()
    row = db.query(f'{SELECT} WHERE p.id=%s', (pid,), one=True)
    return jsonify(product_to_dict(row)) if row else err('Produto não encontrado.', 404)


@bp.delete('/products/<int:pid>')
@admin_required
def delete_product(pid):
    if not db.query('SELECT id FROM products WHERE id=%s', (pid,), one=True):
        return err('Produto não encontrado.', 404)
    used = db.query('SELECT COUNT(*) AS n FROM order_items WHERE product_id=%s', (pid,), one=True)['n']
    if used:
        db.execute('UPDATE products SET active=0 WHERE id=%s', (pid,))
        db.commit()
        return jsonify({'deleted': False, 'message': 'Produto tem pedidos e foi apenas desativado.'})
    db.execute('DELETE FROM products WHERE id=%s', (pid,))
    db.commit()
    return jsonify({'deleted': True, 'message': 'Produto excluído.'})


@bp.get('/orders')
@admin_required
def list_orders():
    status = request.args.get('status')
    where, params = '', []
    if status in STATUSES:
        where, params = ' WHERE o.status=%s', [status]
    orders = db.query(
        'SELECT o.*, u.name AS customer_name, u.email AS customer_email FROM orders o '
        f'JOIN users u ON u.id = o.user_id{where} ORDER BY o.id DESC LIMIT 200', params)
    by_order = {}
    if orders:
        marks = ','.join(['%s'] * len(orders))
        for i in db.query(
                'SELECT oi.order_id, oi.product_id, oi.name, oi.unit_price, oi.quantity, p.image, c.kind '
                'FROM order_items oi JOIN products p ON p.id = oi.product_id '
                f'JOIN categories c ON c.id = p.category_id WHERE oi.order_id IN ({marks})',
                [o['id'] for o in orders]):
            by_order.setdefault(i['order_id'], []).append(i)
    out = []
    for o in orders:
        data = format_order(o, by_order.get(o['id'], []))
        data['customer'] = {'name': o['customer_name'], 'email': o['customer_email']}
        out.append(data)
    return jsonify(out)


@bp.patch('/orders/<int:oid>/status')
@admin_required
def set_status(oid):
    status = (request.get_json(silent=True) or {}).get('status')
    order = db.query('SELECT status FROM orders WHERE id=%s', (oid,), one=True)
    if not order:
        return err('Pedido não encontrado.', 404)
    if status not in STATUSES:
        return err('Status inválido.')
    if order['status'] == 'cancelled' and status != 'cancelled':
        return err('Pedidos cancelados não podem ser reabertos (o estoque já foi devolvido).', 409)
    if status == 'cancelled':
        cancel_and_restock(oid)
    else:
        db.execute('UPDATE orders SET status=%s WHERE id=%s', (status, oid))
        db.commit()
    return jsonify({'id': oid, 'status': status})
