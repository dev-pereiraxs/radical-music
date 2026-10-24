"""Acesso ao banco com SQL simples. Use sempre %s como marcador de parâmetro."""
import sqlite3

from flask import g

import config


def connect(with_db=True):
    if config.DB_ENGINE == 'sqlite':
        conn = sqlite3.connect(config.DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn
    import pymysql
    extra = {}
    if config.DB_SSL:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False  # conexão criptografada, sem conferir o certificado
        ctx.verify_mode = ssl.CERT_NONE
        extra['ssl'] = ctx
    return pymysql.connect(
        host=config.DB_HOST, port=config.DB_PORT,
        user=config.DB_USER, password=config.DB_PASSWORD,
        database=config.DB_NAME if with_db else None,
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
        autocommit=False, **extra,
    )


def prep(sql):
    return sql.replace('%s', '?') if config.DB_ENGINE == 'sqlite' else sql


def get_db():
    if 'db' not in g:
        g.db = connect()
    return g.db


def query(sql, params=(), one=False):
    cur = get_db().cursor()
    cur.execute(prep(sql), tuple(params))
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=()):
    """Executa uma alteração. Devolve (id_inserido, linhas_afetadas)."""
    cur = get_db().cursor()
    cur.execute(prep(sql), tuple(params))
    result = (cur.lastrowid, cur.rowcount)
    cur.close()
    return result


def commit():
    get_db().commit()


def rollback():
    get_db().rollback()


def close_db(exc=None):
    conn = g.pop('db', None)
    if conn is not None:
        if exc:
            conn.rollback()
        conn.close()
