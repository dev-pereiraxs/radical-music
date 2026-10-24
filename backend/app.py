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
