import re

from flask import Blueprint, g, jsonify, request

import db
from auth import (err, hash_password, login_required, make_token,
                  public_user, verify_password)

bp = Blueprint('auth', __name__, url_prefix='/api/auth')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


@bp.post('/register')
def register():
    d = request.get_json(silent=True) or {}
    name = str(d.get('name') or '').strip()
    email = str(d.get('email') or '').strip().lower()
    password = str(d.get('password') or '')
    if len(name) < 2:
        return err('Informe seu nome.')
    if not EMAIL_RE.match(email) or len(email) > 160:
        return err('E-mail inválido.')
    if len(password) < 6:
        return err('A senha precisa ter pelo menos 6 caracteres.')
    if db.query('SELECT id FROM users WHERE email=%s', (email,), one=True):
        return err('Já existe uma conta com este e-mail.', 409)
    user_id, _ = db.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)',
        (name[:120], email, hash_password(password)))
    db.commit()
    user = db.query('SELECT id, name, email, is_admin FROM users WHERE id=%s', (user_id,), one=True)
    return jsonify({'token': make_token(user_id), 'user': public_user(user)}), 201


@bp.post('/login')
def login():
    d = request.get_json(silent=True) or {}
    email = str(d.get('email') or '').strip().lower()
    password = str(d.get('password') or '')
    u = db.query('SELECT * FROM users WHERE email=%s', (email,), one=True)
    if not u or not verify_password(u['password_hash'], password):
        return err('E-mail ou senha incorretos.', 401)
    return jsonify({'token': make_token(u['id']), 'user': public_user(u)})


@bp.get('/me')
@login_required
def me():
    return jsonify({'user': public_user(g.user)})
