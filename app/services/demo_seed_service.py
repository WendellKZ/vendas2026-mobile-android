import os

from sqlalchemy.orm import Session

from app.models.product import Product


DEMO_PRODUCTS = [
    {"code": "P001", "name": "Carrinho de Bebê Premium", "category": "Bebê", "unit": "UN", "price": 899.90, "stock": 100},
    {"code": "P002", "name": "Banheira Infantil", "category": "Bebê", "unit": "UN", "price": 129.90, "stock": 120},
    {"code": "P003", "name": "Cadeirão Alimentação", "category": "Bebê", "unit": "UN", "price": 349.90, "stock": 80},
    {"code": "P004", "name": "Berço Portátil", "category": "Bebê", "unit": "UN", "price": 599.90, "stock": 60},
    {"code": "P005", "name": "Kit Mamadeira", "category": "Acessórios", "unit": "KIT", "price": 89.90, "stock": 200},
    {"code": "P006", "name": "Brinquedo Educativo", "category": "Brinquedos", "unit": "UN", "price": 59.90, "stock": 250},
    {"code": "P007", "name": "Bebê Conforto", "category": "Bebê", "unit": "UN", "price": 499.90, "stock": 70},
    {"code": "P008", "name": "Tapete Infantil", "category": "Brinquedos", "unit": "UN", "price": 149.90, "stock": 90},
]


def seed_demo_products(db: Session) -> int:
    created = 0
    for item in DEMO_PRODUCTS:
        product = db.query(Product).filter(Product.code == item["code"]).first()
        if product:
            continue
        db.add(
            Product(
                code=item["code"],
                name=item["name"],
                category=item["category"],
                unit=item["unit"],
                price_table=item["price"],
                stock=item["stock"],
            )
        )
        created += 1
    db.commit()
    return created


def seed_demo_data_if_enabled(db: Session) -> None:
    enabled = os.getenv("SEED_DEMO_DATA", "0").strip().lower() in {"1", "true", "yes", "sim"}
    if not enabled:
        return
    created = seed_demo_products(db)
    print(f"[seed-demo] Produtos demo criados: {created}", flush=True)
