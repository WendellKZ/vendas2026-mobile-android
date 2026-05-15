from app.db.session import SessionLocal
from app.models.product import Product


def run():
    db = SessionLocal()

    produtos = [
        ("P001", "Carrinho de Bebê Premium", 899.90),
        ("P002", "Banheira Infantil", 129.90),
        ("P003", "Cadeirão Alimentação", 349.90),
        ("P004", "Berço Portátil", 599.90),
        ("P005", "Kit Mamadeira", 89.90),
        ("P006", "Brinquedo Educativo", 59.90),
        ("P007", "Bebê Conforto", 499.90),
        ("P008", "Tapete Infantil", 149.90),
    ]

    for code, name, price in produtos:
        exists = db.query(Product).filter_by(code=code).first()
        if not exists:
            db.add(Product(code=code, name=name, price_table=price, stock=100))

    db.commit()
    print("Produtos de demonstração inseridos com sucesso!")


if __name__ == "__main__":
    run()
