from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.auth import hash_password
from app.models import Branch, Company, Customer, Product, User

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    company = db.query(Company).filter_by(name="Lider Brinquedos").first()
    if not company:
        company = Company(name="Lider Brinquedos")
        db.add(company)
        db.commit()
        db.refresh(company)

    branch = db.query(Branch).filter_by(name="Matriz", company_id=company.id).first()
    if not branch:
        branch = Branch(name="Matriz", company_id=company.id)
        db.add(branch)
        db.commit()
        db.refresh(branch)

    admin = db.query(User).filter_by(email="admin@lider.com").first()
    if not admin:
        db.add(User(name="Administrador", email="admin@lider.com", role="admin", password_hash=hash_password("admin123"), active=True, company_id=company.id, branch_id=branch.id))
        db.commit()

    user = db.query(User).filter_by(email="vendedor@lider.com").first()
    if not user:
        db.add(User(name="Vendedor Padrão", email="vendedor@lider.com", role="seller", password_hash=hash_password("123456"), active=True, company_id=company.id, branch_id=branch.id))
        db.commit()

    if db.query(Customer).count() == 0:
        db.add_all([
            Customer(name="Loja Sol", document="12345678000100", city="Santo André", status="ativo"),
            Customer(name="Brinca Mais", document="98765432000100", city="São Paulo", status="prospect"),
        ])
        db.commit()

    if db.query(Product).count() == 0:
        db.add_all([
            Product(code="BRQ001", name="Carrinho Turbo", category="Brinquedos", unit="UN", price_table=99.90, price_minimum=89.90, commission=3, stock=50),
            Product(code="BRQ002", name="Boneca Estrela", category="Brinquedos", unit="UN", price_table=79.90, price_minimum=69.90, commission=3, stock=30),
            Product(code="BRQ003", name="Quebra-Cabeça 1000 peças", category="Educativo", unit="UN", price_table=59.90, price_minimum=49.90, commission=2.5, stock=40),
        ])
        db.commit()

    print("Seed concluído com sucesso.")
finally:
    db.close()
