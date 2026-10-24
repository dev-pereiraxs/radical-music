from flask import Blueprint, jsonify, request

import db
from auth import err
from services import product_to_dict

bp = Blueprint('catalog', __name__, url_prefix='/api')

SELECT = ('SELECT p.*, c.name AS category_name, c.slug AS category_slug, c.kind AS category_kind '
          'FROM products p JOIN categories c ON c.id = p.category_id')


def _num(value):
    try:
        return float(str(value).replace(',', '.'))
    except (TypeError, ValueError):
        return None


@bp.get('/filters')
def filters():
    cats = db.query(
        'SELECT c.id, c.name, c.slug, c.kind, COUNT(p.id) AS count FROM categories c '
        'LEFT JOIN products p ON p.category_id = c.id AND p.active = 1 '
        'GROUP BY c.id, c.name, c.slug, c.kind ORDER BY c.id')
    brands = [r['brand'] for r in db.query(
        "SELECT DISTINCT brand FROM products WHERE active=1 AND brand IS NOT NULL AND brand <> '' ORDER BY brand")]
    price = db.query('SELECT MIN(price) AS mn, MAX(price) AS mx FROM products WHERE active=1', one=True)
    return jsonify({
        'categories': cats, 'brands': brands,
        'price_min': float(price['mn'] or 0), 'price_max': float(price['mx'] or 0),
    })


@bp.get('/products')
def list_products():
    a = request.args
    where, params = ['p.active = 1'], []

    for term in (a.get('search') or '').split()[:6]:
        like = f'%{term}%'
        where.append('(p.name LIKE %s OR p.brand LIKE %s OR p.description LIKE %s OR c.name LIKE %s)')
        params += [like, like, like, like]
    if a.get('category'):
        where.append('c.slug = %s')
        params.append(a['category'])
    if a.get('brand'):
        where.append('p.brand = %s')
        params.append(a['brand'])
    lo, hi = _num(a.get('min_price')), _num(a.get('max_price'))
    if lo is not None:
        where.append('p.price >= %s')
        params.append(lo)
    if hi is not None:
        where.append('p.price <= %s')
        params.append(hi)
    if a.get('in_stock') == '1':
        where.append('p.stock > 0')
    if a.get('featured') == '1':
        where.append('p.featured = 1')

    order = {
        'price_asc': 'p.price ASC', 'price_desc': 'p.price DESC',
        'name': 'p.name ASC', 'newest': 'p.id DESC',
    }.get(a.get('sort'), 'p.featured DESC, p.id ASC')

    try:
        page = max(int(a.get('page', 1)), 1)
        per = min(max(int(a.get('per_page', 12)), 1), 48)
    except ValueError:
        page, per = 1, 12

    w = ' AND '.join(where)
    total = db.query(
        f'SELECT COUNT(*) AS n FROM products p JOIN categories c ON c.id = p.category_id WHERE {w}',
        params, one=True)['n']
    rows = db.query(f'{SELECT} WHERE {w} ORDER BY {order} LIMIT %s OFFSET %s', params + [per, (page - 1) * per])
    return jsonify({
        'items': [product_to_dict(r) for r in rows], 'total': total,
        'page': page, 'pages': max((total + per - 1) // per, 1),
    })


@bp.get('/products/<int:product_id>')
def get_product(product_id):
    row = db.query(f'{SELECT} WHERE p.id = %s AND p.active = 1', (product_id,), one=True)
    if not row:
        return err('Produto não encontrado.', 404)
    return jsonify(product_to_dict(row))
