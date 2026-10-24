import pathlib
import traceback

from flask import Flask, abort, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException

import config
import db
import payments
import routes_admin
import routes_auth
import routes_catalog
import routes_orders

def explain_db_error(code, info):
    """Traduz o código de erro do MySQL numa orientação para o usuário."""
    if not info['host_definido']:
        return 'DB_HOST não está definido: no Render, abra Environment e cadastre DB_HOST com o host do Aiven.'
    if not info['senha_definida']:
        return 'DB_PASSWORD não está definida: cadastre a senha do banco em Environment.'
    hints = {
        1045: 'Usuário ou senha do banco incorretos. Copie DB_USER e DB_PASSWORD de novo pelo painel do Aiven, sem espaços.',
        1044: 'O usuário não tem permissão neste banco. Confira DB_USER e DB_NAME.',
        1049: 'O banco informado em DB_NAME não existe. No Aiven use "defaultdb".',
        1146: 'As tabelas não existem neste banco. Rode "python init_db.py" apontando para o Aiven.',
        3159: 'O servidor exige conexão criptografada. Cadastre DB_SSL com o valor true.',
        2003: 'Não foi possível conectar. Confira DB_HOST e DB_PORT e se o serviço do Aiven está Running (ligado).',
        2002: 'Não foi possível conectar. Confira DB_HOST e DB_PORT e se o serviço do Aiven está Running (ligado).',
        2006: 'O servidor encerrou a conexão. Confira DB_SSL=true e se o Aiven está ligado.',
        2013: 'A conexão caiu. Confira se o Aiven está ligado e tente de novo.',
    }
    if code in hints:
        return hints[code]
    if not info['ssl']:
        return 'Erro de conexão. Bancos na nuvem como o Aiven exigem DB_SSL=true: confira essa variável.'
    return f'Erro de banco (código {code}). Veja a aba Logs do Render para a mensagem completa.'


SITE_DIR = pathlib.Path(__file__).parent / 'site'  # site do React já compilado (npm run build)


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.teardown_appcontext(db.close_db)

    for module in (routes_auth, routes_catalog, routes_orders, routes_admin, payments):
        app.register_blueprint(module.bp)

    @app.after_request
    def cors(resp):
        resp.headers['Access-Control-Allow-Origin'] = config.FRONTEND_URL
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        return resp

    @app.get('/api/health')
    def health():
        return jsonify({'ok': True, 'payment_mode': payments.mode()})

    # Diagnóstico do banco: mostra, em português, por que a loja não carrega produtos.
    # Não revela senha, usuário nem endereço do banco.
    @app.get('/api/health/db')
    def health_db():
        info = {
            'banco': config.DB_NAME, 'porta': config.DB_PORT, 'ssl': config.DB_SSL,
            'host_definido': config.DB_HOST not in ('', 'localhost'),
            'senha_definida': bool(config.DB_PASSWORD),
        }
        try:
            products = db.query('SELECT COUNT(*) AS n FROM products', one=True)['n']
            categories = db.query('SELECT COUNT(*) AS n FROM categories', one=True)['n']
        except Exception as e:  # noqa: BLE001
            code = e.args[0] if e.args and isinstance(e.args[0], int) else None
            info.update(ok=False, codigo=code, diagnostico=explain_db_error(code, info))
            return jsonify(info), 500
        info.update(ok=True, produtos=products, categorias=categories)
        if products == 0:
            info['diagnostico'] = 'Conectou, mas não há produtos. Rode "python init_db.py" apontando para este banco.'
        return jsonify(info)

    @app.get('/', defaults={'path': ''})
    @app.get('/<path:path>')
    def site(path):
        """Entrega o site do React (se a pasta 'site' existir). Rotas do React caem no index.html."""
        if path == 'api' or path.startswith('api/'):
            abort(404)
        if not (SITE_DIR / 'index.html').is_file():
            return jsonify({'message': 'API da Radical Music no ar. O site compilado não foi encontrado na pasta backend/site.'})
        if path and (SITE_DIR / path).is_file():
            return send_from_directory(SITE_DIR, path)
        resp = send_from_directory(SITE_DIR, 'index.html')
        resp.headers['Cache-Control'] = 'no-cache'
        return resp

    @app.errorhandler(HTTPException)
    def http_error(e):
        return jsonify({'error': e.description}), e.code

    @app.errorhandler(Exception)
    def unexpected(e):
        traceback.print_exc()
        return jsonify({'error': 'Erro interno do servidor.'}), 500

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)