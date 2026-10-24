"""Cria o banco, as tabelas e os dados iniciais (categorias, produtos de exemplo e o administrador).

Uso:  python init_db.py
Pode ser executado de novo sem problema: só preenche o que estiver vazio.
"""
import pathlib
import re

import config
from auth import hash_password
from db import connect, prep

CATEGORIES = [
    ('Violões', 'violoes', 'violao'),
    ('Guitarras', 'guitarras', 'guitarra'),
    ('Baixos', 'baixos', 'baixo'),
    ('Baterias', 'baterias', 'bateria'),
    ('Teclados', 'teclados', 'teclado'),
    ('Cordas', 'cordas', 'cordas'),
    ('Acessórios', 'acessorios', 'acessorios'),
    ('Amplificadores', 'amplificadores', 'amplificador'),
]

# (categoria, nome, marca, preço, estoque, destaque, imagem, descrição)
# Produtos e preços FICTÍCIOS, criados só para demonstração da loja.
PRODUCTS = [
    ('violoes', 'Violão Eletroacústico Ibanez PF15ECE Preto', 'Ibanez', 1899.90, 8, 1, '/products/ibanez-pf15ece.webp',
     'Violão folk com corte (cutaway) e captação para ligar em amplificador, acabamento preto brilhante. Ótimo para estudar em casa e para tocar ao vivo.'),
    ('violoes', 'Violão Clássico Cordas de Nylon Natural', 'Radical', 749.90, 12, 0, None,
     'Violão clássico de tamanho padrão, com cordas de nylon, ideal para quem está começando.'),
    ('violoes', 'Violão Folk Cordas de Aço Sunburst', 'Radical', 899.90, 9, 0, None,
     'Violão folk com cordas de aço e acabamento sunburst.'),
    ('guitarras', 'Guitarra B.C. Rich Warlock Preta', 'B.C. Rich', 2499.90, 4, 1, '/products/bc-rich-warlock.webp',
     'Guitarra de formato agressivo, dois captadores humbucker e acabamento preto. Feita para o rock pesado.'),
    ('guitarras', 'Guitarra Stratocaster Sunburst', 'Radical', 1599.90, 6, 0, None,
     'Guitarra de corpo sólido com três captadores single coil e braço de maple.'),
    ('guitarras', 'Guitarra Single Cut Preta', 'Radical', 1799.90, 5, 0, None,
     'Guitarra de corte único com dois humbuckers e timbre encorpado.'),
    ('baixos', 'Baixo Ibanez Soundgear SR 4 Cordas Roxo Metálico', 'Ibanez', 3299.90, 3, 1, '/products/ibanez-sr-roxo.webp',
     'Baixo de 4 cordas com corpo fino e confortável, captadores ativos e acabamento roxo metálico.'),
    ('baixos', 'Baixo 4 Cordas Passivo Preto', 'Radical', 1399.90, 7, 0, None,
     'Baixo passivo de 4 cordas, ótimo para começar.'),
    ('baterias', 'Bateria Acústica 5 Peças com Pratos e Ferragens', 'Radical', 4599.90, 2, 1, None,
     'Kit completo com bumbo, caixa, dois tons, surdo, pratos e ferragens.'),
    ('baterias', 'Bateria Eletrônica Compacta 8 Pads', 'Radical', 2899.90, 3, 0, None,
     'Bateria eletrônica para estudar sem incomodar os vizinhos, com saída para fone.'),
    ('teclados', 'Teclado Arranjador 61 Teclas', 'Radical', 1799.90, 6, 1, None,
     'Teclado com 61 teclas sensíveis, centenas de timbres e ritmos prontos.'),
    ('teclados', 'Piano Digital 88 Teclas Pesadas', 'Radical', 5299.90, 2, 0, None,
     'Piano digital com 88 teclas de ação martelada e pedal de sustain incluso.'),
    ('cordas', 'Encordoamento para Violão Aço 0.011', 'Radical', 49.90, 80, 0, None,
     'Jogo de cordas de aço para violão, calibre 0.011.'),
    ('cordas', 'Encordoamento para Violão Nylon Tensão Média', 'Radical', 39.90, 60, 0, None,
     'Jogo de cordas de nylon para violão clássico.'),
    ('cordas', 'Encordoamento para Guitarra 0.010', 'Radical', 44.90, 70, 0, None,
     'Jogo de cordas para guitarra, calibre 0.010.'),
    ('cordas', 'Encordoamento para Baixo 4 Cordas 0.045', 'Radical', 119.90, 40, 0, None,
     'Jogo de cordas para baixo de 4 cordas, calibre 0.045.'),
    ('acessorios', 'Kit para Guitarra: Afinador, Capotraste, Suporte e 7 Palhetas', 'Aroma', 79.90, 25, 1, '/products/kit-acessorios.webp',
     'Kit com afinador de clipe, capotraste, suporte de palheta e sete palhetas coloridas.'),
    ('acessorios', 'Suporte Tipo Tripé para Violão e Guitarra', 'Radical', 89.90, 18, 0, None,
     'Suporte dobrável de chão para violão, guitarra ou baixo.'),
    ('acessorios', 'Suporte em X para Teclado', 'Radical', 129.90, 10, 0, None,
     'Suporte em X com altura regulável para teclados e pianos digitais.'),
    ('acessorios', 'Capotraste de Alumínio', 'Radical', 29.90, 45, 0, None,
     'Capotraste de acionamento rápido, serve para violão e guitarra.'),
    ('acessorios', 'Pacote com 12 Palhetas Coloridas', 'Radical', 19.90, 100, 0, None,
     'Palhetas de celuloide em cores variadas, espessura média.'),
    ('acessorios', 'Baquetas 5A de Madeira (par)', 'Radical', 39.90, 60, 0, None,
     'Par de baquetas de madeira, modelo 5A.'),
    ('amplificadores', 'Caixa Amplificada Multiuso LL Audio LX60', 'LL Audio', 649.90, 7, 1, '/products/ll-lx60.webp',
     'Caixa multiuso com entradas para microfone, guitarra/violão e auxiliar, com equalizador.'),
    ('amplificadores', 'Cubo para Guitarra 20W', 'Radical', 499.90, 8, 0, None,
     'Amplificador compacto de 20W com controle de ganho e equalizador.'),
]


def schema_statements():
    sql = (pathlib.Path(__file__).parent / 'schema.sql').read_text(encoding='utf-8')
    if config.DB_ENGINE == 'sqlite':  # adaptação usada apenas nos testes
        sql = re.sub(r'\)\s*ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;', ');', sql)
        sql = sql.replace('INT AUTO_INCREMENT PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
    return [s.strip() for s in sql.split(';') if s.strip()]


def main():
    if config.DB_ENGINE != 'sqlite':
        try:
            root = connect(with_db=False)
            with root.cursor() as cur:
                cur.execute(f'CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` '
                            'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
            root.commit()
            root.close()
        except Exception as e:  # em serviços na nuvem o banco já existe e o usuário pode não ter essa permissão
            print(f'Aviso: não foi possível criar o banco automaticamente ({e}). Usando o banco "{config.DB_NAME}" existente.')

    conn = connect()
    cur = conn.cursor()
    run = lambda sql, params=(): cur.execute(prep(sql), tuple(params))

    for stmt in schema_statements():
        cur.execute(stmt)
    print('Tabelas prontas.')

    cur.execute('SELECT COUNT(*) AS n FROM categories')
    if dict(cur.fetchone())['n'] == 0:
        for name, slug, kind in CATEGORIES:
            run('INSERT INTO categories (name, slug, kind) VALUES (%s, %s, %s)', (name, slug, kind))
        cur.execute('SELECT id, slug FROM categories')
        ids = {dict(r)['slug']: dict(r)['id'] for r in cur.fetchall()}
        for slug, name, brand, price, stock, featured, image, desc in PRODUCTS:
            run('INSERT INTO products (category_id, name, brand, description, price, stock, image, featured) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (ids[slug], name, brand, desc, f'{price:.2f}', stock, image, featured))
        print(f'{len(PRODUCTS)} produtos de exemplo cadastrados.')

    cur.execute(prep('SELECT id FROM users WHERE email=%s'), (config.ADMIN_EMAIL.lower(),))
    if not cur.fetchone():
        run('INSERT INTO users (name, email, password_hash, is_admin) VALUES (%s, %s, %s, 1)',
            ('Administrador', config.ADMIN_EMAIL.lower(), hash_password(config.ADMIN_PASSWORD)))
        print(f'Administrador criado: {config.ADMIN_EMAIL}')

    conn.commit()
    conn.close()
    print('Pronto! Agora rode:  python app.py')


if __name__ == '__main__':
    main()
