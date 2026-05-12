# API Mobile Vendas 2026 - V26 Integração Web
# Patch independente para Flask.
# Objetivo: permitir que o App Android grave pedidos e consulte pelo Web sem quebrar o ERP atual.
#
# Como usar no ERP Web:
# 1) Copie este arquivo para a raiz do projeto Flask, ao lado do app.py/run.py.
# 2) No app.py, após criar o app, adicione:
#      from mobile_api import mobile_api
#      app.register_blueprint(mobile_api)
# 3) Rode o sistema e acesse:
#      http://localhost:5098/mobile/pedidos
#
# Observação:
# Esta V26 salva os pedidos do app em um SQLite separado: mobile_pedidos.db.
# Isso é proposital para não alterar as tabelas atuais do ERP.
# Depois podemos trocar a função salvar_pedido_mobile() para gravar direto nos models reais do ERP.

from flask import Blueprint, jsonify, request, render_template_string
from datetime import datetime
import json
import os
import sqlite3

mobile_api = Blueprint("mobile_api", __name__, url_prefix="")
DB_NAME = os.environ.get("MOBILE_PEDIDOS_DB", "mobile_pedidos.db")


def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mobile_pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT NOT NULL,
                empresa_id TEXT DEFAULT '1',
                empresa_nome TEXT DEFAULT '',
                codigo_cliente TEXT NOT NULL,
                nome_cliente TEXT NOT NULL,
                codigo_transportadora TEXT,
                nome_transportadora TEXT,
                codigo_condicao_pagamento TEXT,
                condicao_pagamento TEXT,
                observacao TEXT,
                total TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Orçamento',
                pode_editar INTEGER NOT NULL DEFAULT 1,
                origem TEXT NOT NULL DEFAULT 'APP_ANDROID',
                itens_json TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
            """
        )
        # Migração leve para bancos criados nas versões anteriores.
        cols = [r[1] for r in conn.execute("PRAGMA table_info(mobile_pedidos)").fetchall()]
        if "empresa_id" not in cols:
            conn.execute("ALTER TABLE mobile_pedidos ADD COLUMN empresa_id TEXT DEFAULT '1'")
        if "empresa_nome" not in cols:
            conn.execute("ALTER TABLE mobile_pedidos ADD COLUMN empresa_nome TEXT DEFAULT ''")
        if "codigo_transportadora" not in cols:
            conn.execute("ALTER TABLE mobile_pedidos ADD COLUMN codigo_transportadora TEXT")
        if "nome_transportadora" not in cols:
            conn.execute("ALTER TABLE mobile_pedidos ADD COLUMN nome_transportadora TEXT")
        if "codigo_condicao_pagamento" not in cols:
            conn.execute("ALTER TABLE mobile_pedidos ADD COLUMN codigo_condicao_pagamento TEXT")
        if "condicao_pagamento" not in cols:
            conn.execute("ALTER TABLE mobile_pedidos ADD COLUMN condicao_pagamento TEXT")
        if "observacao" not in cols:
            conn.execute("ALTER TABLE mobile_pedidos ADD COLUMN observacao TEXT")
        conn.commit()


def row_to_pedido(row):
    return {
        "id": row["id"],
        "numero": row["numero"],
        "cliente": row["nome_cliente"],
        "empresa_id": row["empresa_id"],
        "empresa_nome": row["empresa_nome"],
        "codigo_cliente": row["codigo_cliente"],
        "codigo_transportadora": row["codigo_transportadora"],
        "transportadora": row["nome_transportadora"],
        "codigo_condicao_pagamento": row["codigo_condicao_pagamento"],
        "condicao_pagamento": row["condicao_pagamento"],
        "observacao": row["observacao"],
        "total": row["total"],
        "total_formatado": row["total"],
        "status": row["status"],
        "pode_editar": bool(row["pode_editar"]),
        "origem": row["origem"],
        "criado_em": row["criado_em"],
        "itens": json.loads(row["itens_json"] or "[]"),
    }


def salvar_pedido_mobile(data):
    """
    Ponto central de gravação.
    Nesta versão grava em tabela isolada para evitar risco no ERP.
    Em evolução futura, substituímos esta função para criar Pedido/Itens nas tabelas reais do ERP.
    """
    itens = data.get("itens") or []
    if not data.get("codigo_cliente") or not itens:
        raise ValueError("Cliente e itens são obrigatórios")

    init_db()
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    numero = "APP-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    empresa_id = str(data.get("empresa_id") or request.args.get("empresa_id") or "1")
    empresa_nome = data.get("empresa_nome") or ""
    nome_cliente = data.get("nome_cliente") or data.get("cliente") or "Cliente"
    total = data.get("total") or data.get("total_formatado") or "R$ 0,00"
    codigo_transportadora = data.get("codigo_transportadora") or ""
    nome_transportadora = data.get("nome_transportadora") or data.get("transportadora") or ""
    codigo_condicao_pagamento = data.get("codigo_condicao_pagamento") or ""
    condicao_pagamento = data.get("condicao_pagamento") or ""
    observacao = data.get("observacao") or ""

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO mobile_pedidos
            (numero, empresa_id, empresa_nome, codigo_cliente, nome_cliente, codigo_transportadora, nome_transportadora, codigo_condicao_pagamento, condicao_pagamento, observacao, total, status, pode_editar, origem, itens_json, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                numero,
                empresa_id,
                empresa_nome,
                str(data.get("codigo_cliente")),
                nome_cliente,
                codigo_transportadora,
                nome_transportadora,
                codigo_condicao_pagamento,
                condicao_pagamento,
                observacao,
                total,
                "Orçamento",
                1,
                data.get("origem") or "APP_ANDROID",
                json.dumps(itens, ensure_ascii=False),
                criado_em,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM mobile_pedidos WHERE id = ?", (cur.lastrowid,)).fetchone()
        return row_to_pedido(row)


@mobile_api.route("/api/mobile/login", methods=["POST"])
def mobile_login():
    data = request.get_json(silent=True) or {}
    usuario = data.get("usuario") or data.get("email") or ""
    senha = data.get("senha") or ""
    if not usuario or not senha:
        return jsonify({"erro": "Informe usuário e senha"}), 400

    # V20: login simples para integração mobile. Na próxima etapa conectamos no login real do ERP.
    return jsonify({
        "token": "mobile-token-v9",
        "usuario": {"nome": usuario, "email": usuario, "token": "mobile-token-v9"},
    })


@mobile_api.route("/api/mobile/empresas", methods=["GET"])
def mobile_empresas():
    return jsonify([
        {"codigo": "1", "nome": "Líder Brinquedos", "cnpj": "00.000.000/0001-00", "cidade": "São Bernardo/SP", "destaque": "Catálogo principal"},
        {"codigo": "2", "nome": "Líder Baby", "cnpj": "00.000.000/0002-00", "cidade": "São Paulo/SP", "destaque": "Linha bebê"},
        {"codigo": "3", "nome": "Líder Distribuição", "cnpj": "00.000.000/0003-00", "cidade": "Campinas/SP", "destaque": "Atacado e distribuição"},
    ])


@mobile_api.route("/api/mobile/clientes", methods=["GET"])
def mobile_clientes():
    # Consulta segura para V20. Na V20 trocamos para os clientes reais do ERP.
    return jsonify([
        {"codigo": "CLI001", "nome": "Loja Exemplo Centro", "cidade": "Santo André/SP"},
        {"codigo": "CLI002", "nome": "Mercado Bom Preço", "cidade": "São Paulo/SP"},
        {"codigo": "CLI003", "nome": "Papelaria Primavera", "cidade": "São Bernardo/SP"},
        {"codigo": "CLI004", "nome": "Distribuidora Infantil", "cidade": "Campinas/SP"},
    ])


@mobile_api.route("/api/mobile/transportadoras", methods=["GET"])
def mobile_transportadoras():
    return jsonify([
        {"codigo": "T001", "nome": "Retira / Sem transportadora", "prazo": "Cliente retira", "frete": "R$ 0,00"},
        {"codigo": "T002", "nome": "Rodonaves", "prazo": "3 a 5 dias", "frete": "A combinar"},
        {"codigo": "T003", "nome": "Jadlog", "prazo": "2 a 4 dias", "frete": "A calcular"},
        {"codigo": "T004", "nome": "Braspress", "prazo": "4 a 7 dias", "frete": "A calcular"},
        {"codigo": "T005", "nome": "Transportadora do Cliente", "prazo": "Conforme cliente", "frete": "Por conta cliente"},
    ])


@mobile_api.route("/api/mobile/condicoes-pagamento", methods=["GET"])
def mobile_condicoes_pagamento():
    return jsonify([
        {"codigo": "001", "descricao": "À vista", "prazo": "0 dia"},
        {"codigo": "007", "descricao": "7 dias", "prazo": "7 dias"},
        {"codigo": "014", "descricao": "14 dias", "prazo": "14 dias"},
        {"codigo": "021", "descricao": "21 dias", "prazo": "21 dias"},
        {"codigo": "030", "descricao": "30 dias", "prazo": "30 dias"},
        {"codigo": "283", "descricao": "28/35/42 dias", "prazo": "parcelado"},
    ])


@mobile_api.route("/api/mobile/produtos", methods=["GET"])
def mobile_produtos():
    empresa_id = request.args.get("empresa_id") or "1"
    produtos = [
        {"empresa_id": "1", "codigo": "1001", "nome": "Carrinho Infantil Premium", "estoque": 42, "preco_formatado": "R$ 89,90", "categoria": "Brinquedos", "descricao": "Carrinho infantil com acabamento premium.", "foto_res": "produto_carrinho"},
        {"empresa_id": "1", "codigo": "1002", "nome": "Boneca Coleção Especial", "estoque": 18, "preco_formatado": "R$ 129,90", "categoria": "Bonecas", "descricao": "Boneca de coleção especial com embalagem reforçada.", "foto_res": "produto_boneca"},
        {"empresa_id": "2", "codigo": "2001", "nome": "Kit Bebê Educativo", "estoque": 16, "preco_formatado": "R$ 59,90", "categoria": "Bebê", "descricao": "Kit educativo para bebês.", "foto_res": "produto_bebe"},
        {"empresa_id": "2", "codigo": "2002", "nome": "Mordedor Silicone Bebê", "estoque": 75, "preco_formatado": "R$ 24,90", "categoria": "Bebê", "descricao": "Mordedor de silicone macio.", "foto_res": "produto_mordedor"},
        {"empresa_id": "3", "codigo": "3001", "nome": "Jogo Educativo Cores", "estoque": 31, "preco_formatado": "R$ 44,90", "categoria": "Educativo", "descricao": "Jogo educativo para aprendizagem de cores.", "foto_res": "produto_educativo"},
        {"empresa_id": "3", "codigo": "3002", "nome": "Tapete Atividades Bebê", "estoque": 22, "preco_formatado": "R$ 149,90", "categoria": "Bebê", "descricao": "Tapete de atividades com maior ticket médio.", "foto_res": "produto_tapete"},
    ]
    return jsonify([p for p in produtos if p.get("empresa_id") == empresa_id])


@mobile_api.route("/api/mobile/pedidos", methods=["GET"])
def mobile_pedidos():
    init_db()
    with get_conn() as conn:
        empresa_id = request.args.get("empresa_id")
        if empresa_id:
            rows = conn.execute("SELECT * FROM mobile_pedidos WHERE empresa_id = ? ORDER BY id DESC", (empresa_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM mobile_pedidos ORDER BY id DESC").fetchall()
        pedidos_app = [row_to_pedido(r) for r in rows]
    pedidos_exemplo = [
        {"numero": "1001", "cliente": "Loja Exemplo Centro", "total_formatado": "R$ 499,00", "status": "Aprovado", "pode_editar": True, "empresa_id": empresa_id or "1"},
        {"numero": "1002", "cliente": "Mercado Bom Preço", "total_formatado": "R$ 899,00", "status": "Integrado", "pode_editar": False, "empresa_id": empresa_id or "1"},
    ]
    return jsonify(pedidos_app + pedidos_exemplo)


@mobile_api.route("/api/mobile/pedidos", methods=["POST"])
def mobile_criar_pedido():
    data = request.get_json(silent=True) or {}
    try:
        pedido = salvar_pedido_mobile(data)
        return jsonify(pedido), 201
    except ValueError as exc:
        return jsonify({"erro": str(exc)}), 400
    except Exception as exc:
        return jsonify({"erro": f"Falha ao salvar pedido mobile: {exc}"}), 500


@mobile_api.route("/mobile/pedidos", methods=["GET"])
def mobile_pedidos_web():
    init_db()
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM mobile_pedidos ORDER BY id DESC").fetchall()
        pedidos = [row_to_pedido(r) for r in rows]

    html = """
    <!doctype html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Pedidos Mobile - Vendas 2026</title>
        <style>
            body{font-family:Arial, sans-serif;background:#f6f8fc;margin:0;color:#0f172a}
            .wrap{max-width:1100px;margin:0 auto;padding:28px}
            .top{background:#2563eb;color:white;padding:26px;border-radius:18px;margin-bottom:22px}
            .top h1{margin:0;font-size:28px}.top p{margin:8px 0 0;opacity:.92}
            .card{background:white;border-radius:16px;padding:20px;margin-bottom:14px;box-shadow:0 8px 22px rgba(15,23,42,.06)}
            .row{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;flex-wrap:wrap}
            .num{font-weight:700;font-size:18px}.muted{color:#64748b;font-size:14px}.total{font-weight:700;color:#2563eb}
            .badge{display:inline-block;padding:6px 10px;border-radius:999px;background:#fef3c7;color:#92400e;font-weight:700;font-size:12px}
            pre{background:#f1f5f9;border-radius:12px;padding:12px;overflow:auto;font-size:12px}
        </style>
    </head>
    <body><div class="wrap">
        <div class="top"><h1>Pedidos Mobile</h1><p>Pedidos enviados pelo App Android Vendas 2026 - V20.</p></div>
        {% if not pedidos %}<div class="card">Nenhum pedido mobile recebido ainda.</div>{% endif %}
        {% for p in pedidos %}
        <div class="card">
            <div class="row">
                <div>
                    <div class="num">{{ p.numero }}</div>
                    <div class="muted">{{ p.cliente }} • {{ p.codigo_cliente }}</div>
                    <div class="muted">Transportadora: {{ p.transportadora or "não informada" }}</div>
                    <div class="muted">Criado em {{ p.criado_em }}</div>
                </div>
                <div><span class="badge">{{ p.status }}</span></div>
                <div class="total">{{ p.total }}</div>
            </div>
            <pre>{{ p.itens | tojson(indent=2) }}</pre>
        </div>
        {% endfor %}
    </div></body></html>
    """
    return render_template_string(html, pedidos=pedidos)
