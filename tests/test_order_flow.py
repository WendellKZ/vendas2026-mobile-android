def test_complete_order_flow(client):
    company = client.post("/api/v1/companies/", json={"name": "Empresa Teste"}).json()
    branch = client.post("/api/v1/branches/", json={"company_id": company["id"], "name": "Filial 1"}).json()
    category = client.post("/api/v1/categories/", json={"name": "Linha A"}).json()
    user = client.post(
        "/api/v1/users/",
        json={
            "company_id": company["id"],
            "name": "Vendedor 1",
            "email": "vendedor1@teste.com",
            "role": "vendedor",
            "max_discount_percent": 5,
        },
    ).json()
    product = client.post(
        "/api/v1/products/",
        json={
            "company_id": company["id"],
            "category_id": category["id"],
            "sku": "SKU1",
            "name": "Produto A",
            "unit": "UN",
            "price": 100,
            "min_price": 90,
            "commission_percent": 4,
        },
    ).json()
    table = client.post(
        "/api/v1/price-tables/",
        json={
            "company_id": company["id"],
            "name": "Tabela padrão",
            "is_default": True,
            "items": [{"product_id": product["id"], "price": 100}],
        },
    ).json()
    customer = client.post(
        "/api/v1/customers/",
        json={
            "company_id": company["id"],
            "name": "Cliente 1",
            "document": "12345678900",
            "city": "São Paulo",
            "status": "ativo",
            "segment": "varejo",
            "default_price_table_id": table["id"],
        },
    ).json()
    client.post(
        "/api/v1/stocks/",
        json={"branch_id": branch["id"], "product_id": product["id"], "quantity": 20, "reserved_quantity": 0},
    )

    order = client.post(
        "/api/v1/orders/",
        json={
            "company_id": company["id"],
            "branch_id": branch["id"],
            "customer_id": customer["id"],
            "seller_id": user["id"],
            "payment_condition_id": None,
            "freight_value": 10,
            "items": [{"product_id": product["id"], "quantity": 2, "discount_percent": 3}],
        },
    )
    assert order.status_code == 201
    data = order.json()
    assert data["status"] == "aprovado"
    assert round(data["net_total"], 2) == 204.0
