from app.auth import hash_password


def _auth_headers(client, suffix):
    company = client.post("/api/v1/companies/", json={"name": f"Mobile Empresa {suffix}"}).json()
    user = client.post(
        "/api/v1/users/",
        json={
            "company_id": company["id"],
            "name": f"Representante Mobile {suffix}",
            "email": f"mobile-{suffix.lower()}@teste.com",
            "role": "vendedor",
            "password_hash": hash_password("123456"),
        },
    ).json()
    login = client.post("/api/mobile/login", json={"usuario": user["email"], "senha": "123456"})
    assert login.status_code == 200
    token = login.json()["token"]
    return company, {"Authorization": f"Bearer {token}"}


def _android_payload(company_id, tipo_finalizacao):
    return {
        "empresa_id": str(company_id),
        "empresa_nome": "Mobile Empresa",
        "codigo_cliente": "APP-NOVO",
        "nome_cliente": f"Cliente {tipo_finalizacao}",
        "codigo_transportadora": "",
        "nome_transportadora": "Transportadora App",
        "codigo_condicao_pagamento": "",
        "condicao_pagamento": "A vista",
        "observacao": "Pedido criado pelo app Android",
        "total": "R$ 190,00",
        "origem": "APP_ANDROID",
        "tipo_finalizacao": tipo_finalizacao,
        "acao": tipo_finalizacao,
        "status_solicitado": "EM_APROVACAO" if tipo_finalizacao == "APROVACAO" else "ORCAMENTO",
        "manter_orcamento": tipo_finalizacao == "ORCAMENTO",
        "itens": [
            {
                "codigo_produto": f"APP-{tipo_finalizacao}",
                "nome_produto": f"Produto {tipo_finalizacao}",
                "quantidade": 2,
                "preco_unitario": "R$ 100,00",
                "desconto_percentual": 5,
                "subtotal_com_desconto": "R$ 190,00",
            }
        ],
    }


def test_android_order_budget_is_created_and_returned_in_mobile_status(client):
    company, headers = _auth_headers(client, "Orcamento")

    response = client.post(
        "/api/mobile/pedidos",
        json=_android_payload(company["id"], "ORCAMENTO"),
        headers=headers,
    )

    assert response.status_code == 200
    created = response.json()
    assert created["confirmado_erp"] is True
    assert created["status"] == "em_orcamento"

    listing = client.get(f"/api/mobile/pedidos?empresa_id={company['id']}", headers=headers)
    assert listing.status_code == 200
    rows = listing.json()
    assert any(row["numero"] == created["numero"] and row["status"] == "em_orcamento" for row in rows)


def test_android_order_approval_is_created_and_returned_with_approval_status(client):
    company, headers = _auth_headers(client, "Aprovacao")

    response = client.post(
        "/api/mobile/pedidos",
        json=_android_payload(company["id"], "APROVACAO"),
        headers=headers,
    )

    assert response.status_code == 200
    created = response.json()
    assert created["confirmado_erp"] is True
    assert created["status"] == "em_aprovacao"

    listing = client.get(f"/api/mobile/pedidos?empresa_id={company['id']}", headers=headers)
    assert listing.status_code == 200
    rows = listing.json()
    assert any(row["numero"] == created["numero"] and row["status"] == "em_aprovacao" for row in rows)
