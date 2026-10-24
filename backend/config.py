import os
from dotenv import load_dotenv

load_dotenv()


def env(key, default=''):
    return os.environ.get(key, default)


# "sqlite" existe só para testes automáticos; o projeto usa MySQL.
DB_ENGINE = env('DB_ENGINE', 'mysql')
DB_HOST = env('DB_HOST', 'localhost')
DB_PORT = int(env('DB_PORT', '3306') or 3306)
DB_USER = env('DB_USER', 'root')
DB_PASSWORD = env('DB_PASSWORD', '')
DB_NAME = env('DB_NAME', 'radical_music')
# Bancos na nuvem (como o Aiven) exigem conexão criptografada.
DB_SSL = env('DB_SSL', '').strip().lower() in ('1', 'true', 'yes', 'sim')

SECRET_KEY = env('SECRET_KEY', 'dev-secret-troque-em-producao')
TOKEN_HOURS = int(env('TOKEN_HOURS', '24') or 24)
FRONTEND_URL = env('FRONTEND_URL', 'http://localhost:5173').rstrip('/')

ADMIN_EMAIL = env('ADMIN_EMAIL', 'admin@radicalmusic.com')
ADMIN_PASSWORD = env('ADMIN_PASSWORD', 'admin123')

MP_ACCESS_TOKEN = env('MP_ACCESS_TOKEN', '').strip()
MP_NOTIFICATION_URL = env('MP_NOTIFICATION_URL', '').strip()
