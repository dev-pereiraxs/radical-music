import functools
from datetime import datetime, timedelta, timezone

import jwt
from flask import g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

import config
import db


def err(message, code=400):
    return jsonify({'error': message}), code


def hash_password(password):
    return generate_password_hash(password, method='pbkdf2:sha256')


def verify_password(hashed, password):
    return check_password_hash(hashed, password)


def make_token(user_id):
    payload = {
        'sub': str(user_id),
        'exp': datetime.now(timezone.utc) + timedelta(hours=config.TOKEN_HOURS),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')


def current_user():
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    try:
        data = jwt.decode(header[7:], config.SECRET_KEY, algorithms=['HS256'])
        user_id = int(data['sub'])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
    return db.query('SELECT id, name, email, is_admin FROM users WHERE id=%s', (user_id,), one=True)


def public_user(u):
    return {'id': u['id'], 'name': u['name'], 'email': u['email'], 'is_admin': bool(u['is_admin'])}


def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return err('Faça login para continuar.', 401)
        g.user = user
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return err('Faça login para continuar.', 401)
        if not user['is_admin']:
            return err('Acesso restrito a administradores.', 403)
        g.user = user
        return fn(*args, **kwargs)
    return wrapper
