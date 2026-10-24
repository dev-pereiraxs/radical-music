"""Funções compartilhadas: serialização de dados, estoque e pagamento de pedidos."""
import db

STATUSES = ['pending_payment', 'paid', 'shipped', 'delivered', 'cancelled']


def iso(value):
    return value.isoformat() if hasattr(value, 'isoformat') else value


def product_to_dict(p):
    return {
        'id': p['id'], 'name': p['name'], 'brand': p.get('brand') or '',
        'description': p.get('description') or '', 'price': float(p['price']),
        'stock': int(p['stock']), 'image': p.get('image') or None,
        'featured': bool(p['featured']), 'active': bool(p['active']),
        'category': {
            'id': p['category_id'], 'name': p.get('category_name'),
            'slug': p.get('category_slug'), 'kind': p.get('category_kind'),
        },
    }


def format_order(o, items):
    return {
        'id': o['id'], 'status': o['status'], 'total': float(o['total']),
        'created_at': iso(o['created_at']), 'paid_at': iso(o.get('paid_at')),
        'payment_provider': o.get('payment_provider'), 'payment_id': o.get('payment_id'),
        'shipping': {
            'name': o['ship_name'], 'zip': o['ship_zip'], 'street': o['ship_street'],
            'number': o['ship_number'], 'complement': o.get('ship_complement') or '',
            'district': o.get('ship_district') or '', 'city': o['ship_city'], 'state': o['ship_state'],
        },
        'items': [{
            'product_id': i['product_id'], 'name': i['name'], 'quantity': int(i['quantity']),
            'unit_price': float(i['unit_price']), 'image': i.get('image'), 'kind': i.get('kind'),
        } for i in items],
    }


def order_items(order_id):
    return db.query(
        'SELECT oi.product_id, oi.name, oi.unit_price, oi.quantity, p.image, c.kind '
        'FROM order_items oi JOIN products p ON p.id = oi.product_id '
        'JOIN categories c ON c.id = p.category_id WHERE oi.order_id=%s ORDER BY oi.id',
        (order_id,))


def get_order(order_id):
    o = db.query('SELECT * FROM orders WHERE id=%s', (order_id,), one=True)
    return format_order(o, order_items(order_id)) if o else None


def mark_paid(order_id, provider, payment_id):
    """Marca como pago (só se ainda estiver aguardando pagamento)."""
    _, changed = db.execute(
        "UPDATE orders SET status='paid', payment_provider=%s, payment_id=%s, paid_at=CURRENT_TIMESTAMP "
        "WHERE id=%s AND status='pending_payment'", (provider, payment_id, order_id))
    db.commit()
    return changed > 0


def cancel_and_restock(order_id):
    """Cancela o pedido e devolve os itens ao estoque. Devolve False se já estava cancelado."""
    o = db.query('SELECT status FROM orders WHERE id=%s', (order_id,), one=True)
    if not o or o['status'] == 'cancelled':
        return False
    for i in db.query('SELECT product_id, quantity FROM order_items WHERE order_id=%s', (order_id,)):
        db.execute('UPDATE products SET stock = stock + %s WHERE id=%s', (i['quantity'], i['product_id']))
    db.execute("UPDATE orders SET status='cancelled' WHERE id=%s", (order_id,))
    db.commit()
    return True
