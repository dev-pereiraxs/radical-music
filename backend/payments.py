"""Pagamentos: Mercado Pago (ambiente de teste) ou pagamento simulado quando não há token."""
import re
import uuid

import requests
from flask import Blueprint, g, jsonify, request

import config
import db
from auth import err, login_required
from services import get_order, mark_paid

bp = Blueprint('payments', __name__, url_prefix='/api/payments')
MP_API = 'https://api.mercadopago.com'


class PaymentError(Exception):
    pass


def mode():
    return 'mercadopago' if config.MP_ACCESS_TOKEN else 'simulated'


def _headers():
    return {'Authorization': f'Bearer {config.MP_ACCESS_TOKEN}', 'Content-Type': 'application/json'}


def start_checkout(order):
    """Devolve o endereço para onde o cliente deve ir para pagar."""
    if mode() == 'simulated':
        return {'mode': 'simulated', 'checkout_url': f"{config.FRONTEND_URL}/pagamento/{order['id']}"}

    back = f"{config.FRONTEND_URL}/pedido/{order['id']}"
    body = {
        'items': [{
            'id': str(i['product_id']), 'title': i['name'][:250], 'quantity': i['quantity'],
            'unit_price': round(i['unit_price'], 2), 'currency_id': 'BRL',
        } for i in order['items']],
        'external_reference': str(order['id']),
        'back_urls': {'success': back, 'failure': back, 'pending': back},
        'statement_descriptor': 'RADICAL MUSIC',
    }
    if config.MP_NOTIFICATION_URL:
        body['notification_url'] = config.MP_NOTIFICATION_URL
    try:
        r = requests.post(f'{MP_API}/checkout/preferences', json=body, headers=_headers(), timeout=20)
    except requests.RequestException:
        raise PaymentError('Não foi possível falar com o Mercado Pago. Tente novamente.')
    if r.status_code not in (200, 201):
        raise PaymentError('O Mercado Pago recusou a criação do pagamento. Confira o MP_ACCESS_TOKEN.')
    data = r.json()
    url = data.get('init_point') or data.get('sandbox_init_point')
    if not url:
        raise PaymentError('Resposta inesperada do Mercado Pago.')
    return {'mode': 'mercadopago', 'checkout_url': url}


def _fetch_payment(payment_id):
    try:
        r = requests.get(f'{MP_API}/v1/payments/{payment_id}', headers=_headers(), timeout=20)
    except requests.RequestException:
        raise PaymentError('Não foi possível consultar o pagamento.')
    if r.status_code != 200:
        raise PaymentError('Pagamento não encontrado.')
    return r.json()


def confirm_payment(order, payment_id):
    """Confere o pagamento direto na API do Mercado Pago. Devolve 'paid', 'pending' ou 'rejected'."""
    if mode() != 'mercadopago':
        raise PaymentError('Confirmação disponível apenas com o Mercado Pago ativo.')
    if not re.fullmatch(r'\d{1,20}', str(payment_id or '')):
        raise PaymentError('Identificador de pagamento inválido.')
    p = _fetch_payment(payment_id)
    if str(p.get('external_reference')) != str(order['id']):
        raise PaymentError('Este pagamento não pertence ao pedido.')
    status = p.get('status')
    if status == 'approved':
        mark_paid(order['id'], 'mercadopago', str(payment_id))
        return 'paid'
    return 'rejected' if status in ('rejected', 'cancelled') else 'pending'


@bp.post('/webhook')
def webhook():
    """O Mercado Pago avisa aqui quando um pagamento muda. Sempre confirmamos na API deles."""
    body = request.get_json(silent=True) or {}
    pid = (body.get('data') or {}).get('id') or request.args.get('data.id') or request.args.get('id')
    if pid and mode() == 'mercadopago' and re.fullmatch(r'\d{1,20}', str(pid)):
        try:
            p = _fetch_payment(pid)
            ref = str(p.get('external_reference') or '')
            if p.get('status') == 'approved' and ref.isdigit():
                mark_paid(int(ref), 'mercadopago', str(pid))
        except PaymentError:
            pass
    return jsonify({'ok': True})


@bp.post('/simulate')
@login_required
def simulate():
    """Pagamento simulado (só existe quando NÃO há MP_ACCESS_TOKEN). Nenhum dado de cartão é guardado."""
    if mode() != 'simulated':
        return err('Pagamento simulado desativado.', 404)
    data = request.get_json(silent=True) or {}
    try:
        order_id = int(data.get('order_id'))
    except (TypeError, ValueError):
        return err('Pedido inválido.')
    order = get_order(order_id)
    if not order or not _owns(order_id):
        return err('Pedido não encontrado.', 404)
    if order['status'] != 'pending_payment':
        return err('Este pedido não está aguardando pagamento.', 409)
    digits = re.sub(r'\D', '', str(data.get('card_number') or ''))
    if not 13 <= len(digits) <= 19:
        return err('Número de cartão inválido.')
    if digits.endswith('0002'):
        return jsonify({'status': 'rejected', 'message': 'Pagamento recusado pelo emissor (cartão de teste).'})
    mark_paid(order_id, 'simulated', 'SIM-' + uuid.uuid4().hex[:12].upper())
    return jsonify({'status': 'paid'})


def _owns(order_id):
    row = db.query('SELECT user_id FROM orders WHERE id=%s', (order_id,), one=True)
    return bool(row) and row['user_id'] == g.user['id']
