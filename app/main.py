from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from pathlib import Path
import time
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from app.auth import hash_password

from app.api.routes.branches import router as branches_router
from app.api.routes.carriers import router as carriers_router, web_router as carriers_web_router
from app.api.routes.categories import router as categories_router
from app.api.routes.companies import router as companies_router, web_router as companies_web_router
from app.api.routes.customers import router as customers_router, web_router as customers_web_router
from app.api.routes.orders import router as orders_router, web_router as orders_web_router
from app.api.routes.payment_conditions import router as payment_conditions_router
from app.api.routes.products import router as products_router, web_router as products_web_router
from app.api.routes.price_tables import router as price_tables_router
from app.api.routes.stocks import router as stocks_router
from app.api.routes.users import router as users_router, web_router as users_web_router
from app.api.routes.web import router as web_router
from app.api.routes.rules import web_router as rules_web_router
from app.api.routes.assistant_order import web_router as assistant_order_web_router
from app.api.routes.reports import web_router as reports_web_router
from app.api.routes.company_context import web_router as company_context_web_router
from app.api.routes.mobile_compat import router as mobile_compat_router
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.auth import current_user_from_cookie
import app.models  # noqa: F401


# -----------------------------------------------------------------------------
# Auto-migration leve para desenvolvimento/local/Render
# -----------------------------------------------------------------------------
# Evita tela vazia quando o banco antigo não possui colunas novas.
# Não substitui Alembic em produção, mas ajuda muito na evolução rápida do MVP.


def _dialect() -> str:
    return engine.dialect.name


def _varchar(size: int = 150) -> str:
    return f"VARCHAR({size})"


def _float() -> str:
    return "DOUBLE PRECISION" if _dialect() == "postgresql" else "FLOAT"


def _bool_default_true() -> str:
    return "BOOLEAN DEFAULT TRUE" if _dialect() == "postgresql" else "BOOLEAN DEFAULT 1"


def _int_null() -> str:
    return "INTEGER NULL"


def _timestamp_null() -> str:
    return "TIMESTAMP NULL"


def _columns(table_name: str) -> set[str]:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table_name)}


def _add_columns(table_name: str, statements: dict[str, str]) -> None:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return

    existing = _columns(table_name)

    with engine.begin() as conn:
        for col, stmt in statements.items():
            if col not in existing:
                try:
                    conn.execute(text(stmt))
                    print(f"[auto-migration] {table_name}.{col} criado", flush=True)
                except SQLAlchemyError as exc:
                    print(f"[auto-migration] aviso ao criar {table_name}.{col}: {exc}", flush=True)


def _safe_execute(sql: str, params: dict | None = None) -> None:
    try:
        with engine.begin() as conn:
            conn.execute(text(sql), params or {})
    except SQLAlchemyError as exc:
        print(f"[auto-migration] aviso SQL ignorado: {exc}", flush=True)


def ensure_customer_columns() -> None:
    _add_columns(
        "customers",
        {
            "company_id": f"ALTER TABLE customers ADD COLUMN company_id {_int_null()}",
            "name": f"ALTER TABLE customers ADD COLUMN name {_varchar(180)}",
            "document": f"ALTER TABLE customers ADD COLUMN document {_varchar(40)}",
            "email": f"ALTER TABLE customers ADD COLUMN email {_varchar(150)}",
            "phone": f"ALTER TABLE customers ADD COLUMN phone {_varchar(40)}",
            "city": f"ALTER TABLE customers ADD COLUMN city {_varchar(80)}",
            "state": f"ALTER TABLE customers ADD COLUMN state {_varchar(30)}",
            "corporate_name": f"ALTER TABLE customers ADD COLUMN corporate_name {_varchar(180)}",
            "state_registration": f"ALTER TABLE customers ADD COLUMN state_registration {_varchar(40)}",
            "delivery_location": f"ALTER TABLE customers ADD COLUMN delivery_location {_varchar(180)}",
            "billing_email": f"ALTER TABLE customers ADD COLUMN billing_email {_varchar(150)}",
            "suframa": f"ALTER TABLE customers ADD COLUMN suframa {_varchar(30)}",
            "suframa_status": f"ALTER TABLE customers ADD COLUMN suframa_status {_varchar(30)}",
            "suframa_fonte": f"ALTER TABLE customers ADD COLUMN suframa_fonte {_varchar(50)}",
            "suframa_consultado_em": f"ALTER TABLE customers ADD COLUMN suframa_consultado_em {_timestamp_null()}",
            "suframa_modo": f"ALTER TABLE customers ADD COLUMN suframa_modo {_varchar(20)}",
        },
    )


def ensure_order_columns() -> None:
    _add_columns(
        "orders",
        {
            "company_id": f"ALTER TABLE orders ADD COLUMN company_id {_int_null()}",
            "customer_id": f"ALTER TABLE orders ADD COLUMN customer_id {_int_null()}",
            "seller_id": f"ALTER TABLE orders ADD COLUMN seller_id {_int_null()}",
            "carrier_id": f"ALTER TABLE orders ADD COLUMN carrier_id {_int_null()}",
            "status": f"ALTER TABLE orders ADD COLUMN status {_varchar(30)} DEFAULT 'em_orcamento'",
            "payment_condition": f"ALTER TABLE orders ADD COLUMN payment_condition {_varchar(80)}",
            "delivery_location": f"ALTER TABLE orders ADD COLUMN delivery_location {_varchar(180)}",
            "freight_value": f"ALTER TABLE orders ADD COLUMN freight_value {_float()} DEFAULT 0",
            "total_gross": f"ALTER TABLE orders ADD COLUMN total_gross {_float()} DEFAULT 0",
            "total_discount": f"ALTER TABLE orders ADD COLUMN total_discount {_float()} DEFAULT 0",
            "total_net": f"ALTER TABLE orders ADD COLUMN total_net {_float()} DEFAULT 0",
            "created_at": f"ALTER TABLE orders ADD COLUMN created_at {_timestamp_null()}",
            "commission_percent": f"ALTER TABLE orders ADD COLUMN commission_percent {_float()} DEFAULT 0",
            "commission_total": f"ALTER TABLE orders ADD COLUMN commission_total {_float()} DEFAULT 0",
            "approval_required_role": f"ALTER TABLE orders ADD COLUMN approval_required_role {_varchar(30)}",
            "max_discount_applied": f"ALTER TABLE orders ADD COLUMN max_discount_applied {_float()} DEFAULT 0",
            "rule_summary": f"ALTER TABLE orders ADD COLUMN rule_summary {_varchar(255)}",
        },
    )

    _safe_execute("UPDATE orders SET status = 'em_orcamento' WHERE status IS NULL OR status = ''")
    _safe_execute("UPDATE orders SET total_gross = 0 WHERE total_gross IS NULL")
    _safe_execute("UPDATE orders SET total_discount = 0 WHERE total_discount IS NULL")
    _safe_execute("UPDATE orders SET total_net = COALESCE(total_net, total_gross, 0)")
    _safe_execute("UPDATE orders SET commission_percent = 0 WHERE commission_percent IS NULL")
    _safe_execute("UPDATE orders SET commission_total = 0 WHERE commission_total IS NULL")


def ensure_order_item_columns() -> None:
    _add_columns(
        "order_items",
        {
            "order_id": f"ALTER TABLE order_items ADD COLUMN order_id {_int_null()}",
            "product_id": f"ALTER TABLE order_items ADD COLUMN product_id {_int_null()}",
            "quantity": "ALTER TABLE order_items ADD COLUMN quantity INTEGER DEFAULT 1",
            "unit_price": f"ALTER TABLE order_items ADD COLUMN unit_price {_float()} DEFAULT 0",
            "discount": f"ALTER TABLE order_items ADD COLUMN discount {_float()} DEFAULT 0",
            "total": f"ALTER TABLE order_items ADD COLUMN total {_float()} DEFAULT 0",
        },
    )


def ensure_commercial_rule_columns() -> None:
    Base.metadata.create_all(bind=engine)

    try:
        from app.models.commercial_rule import CommercialRule

        db = SessionLocal()
        try:
            if db.query(CommercialRule).count() == 0:
                db.add(
                    CommercialRule(
                        name="Regra global padrão de desconto",
                        rule_type="discount",
                        scope="global",
                        priority=1,
                        max_discount_percent=5,
                        approval_limit_manager=5,
                        approval_limit_admin=10,
                        active=True,
                    )
                )
                db.add(
                    CommercialRule(
                        name="Comissão global padrão",
                        rule_type="commission",
                        scope="global",
                        priority=1,
                        commission_percent=5,
                        commission_high_discount_percent=2,
                        active=True,
                    )
                )
                db.commit()
        finally:
            db.close()
    except Exception as exc:
        print(f"[auto-migration] aviso regras padrão: {exc}", flush=True)


def ensure_user_columns() -> None:
    _add_columns(
        "users",
        {
            "name": f"ALTER TABLE users ADD COLUMN name {_varchar(120)}",
            "email": f"ALTER TABLE users ADD COLUMN email {_varchar(150)}",
            "role": f"ALTER TABLE users ADD COLUMN role {_varchar(40)} DEFAULT 'seller'",
            "password_hash": f"ALTER TABLE users ADD COLUMN password_hash {_varchar(160)}",
            "active": f"ALTER TABLE users ADD COLUMN active {_bool_default_true()}",
            "company_id": f"ALTER TABLE users ADD COLUMN company_id {_int_null()}",
            "branch_id": f"ALTER TABLE users ADD COLUMN branch_id {_int_null()}",
        },
    )

    _safe_execute("UPDATE users SET role = 'seller' WHERE role IS NULL OR role = ''")

    if _dialect() == "postgresql":
        _safe_execute("UPDATE users SET active = TRUE WHERE active IS NULL")
    else:
        _safe_execute("UPDATE users SET active = 1 WHERE active IS NULL")

    _safe_execute(
        "UPDATE users SET password_hash = :ph WHERE password_hash IS NULL OR password_hash = ''",
        {"ph": hash_password("123456")},
    )
    _safe_execute("UPDATE users SET name = COALESCE(NULLIF(name, ''), 'Vendedor')")

    try:
        with engine.begin() as conn:
            admin_count = conn.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin'")).scalar() or 0
            if admin_count == 0:
                conn.execute(
                    text(
                        "INSERT INTO users (name, email, role, password_hash, active) "
                        "VALUES (:name, :email, 'admin', :ph, :active)"
                    ),
                    {
                        "name": "Administrador",
                        "email": "admin@lider.com",
                        "ph": hash_password("admin123"),
                        "active": True,
                    },
                )
                print("[auto-migration] usuário admin criado: admin@lider.com / admin123", flush=True)

            seller_count = conn.execute(text("SELECT COUNT(*) FROM users WHERE role = 'seller'")).scalar() or 0
            if seller_count == 0:
                conn.execute(
                    text(
                        "INSERT INTO users (name, email, role, password_hash, active) "
                        "VALUES (:name, :email, 'seller', :ph, :active)"
                    ),
                    {
                        "name": "Vendedor Padrão",
                        "email": "vendedor@lider.com",
                        "ph": hash_password("123456"),
                        "active": True,
                    },
                )
                print("[auto-migration] vendedor padrão criado: vendedor@lider.com / 123456", flush=True)
    except SQLAlchemyError as exc:
        print(f"[auto-migration] aviso ao criar usuários padrão: {exc}", flush=True)


def ensure_product_columns() -> None:
    _add_columns(
        "products",
        {
            "company_id": f"ALTER TABLE products ADD COLUMN company_id {_int_null()}",
            "category_id": f"ALTER TABLE products ADD COLUMN category_id {_int_null()}",
            "name": f"ALTER TABLE products ADD COLUMN name {_varchar(180)}",
            "sku": f"ALTER TABLE products ADD COLUMN sku {_varchar(80)}",
            "description": f"ALTER TABLE products ADD COLUMN description {_varchar(255)}",
            "category": f"ALTER TABLE products ADD COLUMN category {_varchar(80)}",
            "unit": f"ALTER TABLE products ADD COLUMN unit {_varchar(20)} DEFAULT 'UN'",
            "price": f"ALTER TABLE products ADD COLUMN price {_float()} DEFAULT 0",
            "price_minimum": f"ALTER TABLE products ADD COLUMN price_minimum {_float()} DEFAULT 0",
            "commission": f"ALTER TABLE products ADD COLUMN commission {_float()} DEFAULT 0",
            "stock": f"ALTER TABLE products ADD COLUMN stock {_float()} DEFAULT 0",
            "active": f"ALTER TABLE products ADD COLUMN active {_bool_default_true()}",
        },
    )


def ensure_carrier_columns() -> None:
    _add_columns(
        "carriers",
        {
            "company_id": f"ALTER TABLE carriers ADD COLUMN company_id {_int_null()}",
            "name": f"ALTER TABLE carriers ADD COLUMN name {_varchar(120)}",
            "document": f"ALTER TABLE carriers ADD COLUMN document {_varchar(40)}",
            "city": f"ALTER TABLE carriers ADD COLUMN city {_varchar(80)}",
            "phone": f"ALTER TABLE carriers ADD COLUMN phone {_varchar(40)}",
            "email": f"ALTER TABLE carriers ADD COLUMN email {_varchar(150)}",
            "active": f"ALTER TABLE carriers ADD COLUMN active {_bool_default_true()}",
        },
    )


def seed_demo_data() -> None:
    try:
        from app.services.demo_seed_service import seed_demo_data_if_enabled

        db = SessionLocal()
        try:
            seed_demo_data_if_enabled(db)
        finally:
            db.close()
    except Exception as exc:
        print(f"[seed-demo] aviso ignorado: {exc}", flush=True)


def init_database_with_retry() -> None:
    last_error = None

    for attempt in range(1, 16):
        try:
            print(f"[startup] Inicializando banco ({_dialect()})...", flush=True)

            Base.metadata.create_all(bind=engine)

            ensure_customer_columns()
            ensure_user_columns()
            ensure_product_columns()
            ensure_carrier_columns()
            ensure_order_columns()
            ensure_order_item_columns()
            ensure_commercial_rule_columns()

            seed_demo_data()

            try:
                from app.services.company_context_service import ensure_default_company_links
                db = SessionLocal()
                try:
                    ensure_default_company_links(db)
                finally:
                    db.close()
            except Exception as exc:
                print(f"[startup] aviso multiempresa: {exc}", flush=True)

            print("[startup] Banco pronto.", flush=True)
            return
        except Exception as exc:
            last_error = exc
            print(f"[startup] Banco ainda não disponível, tentativa {attempt}/15: {exc}", flush=True)
            time.sleep(2)

    raise RuntimeError(f"Não foi possível inicializar o banco de dados: {last_error}")


ROOT_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="ERP Vendas Completo")
app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")
app.state.templates = Jinja2Templates(directory=str(ROOT_DIR / "templates"))


@app.on_event("startup")
def on_startup() -> None:
    init_database_with_retry()


@app.middleware("http")
async def proteger_area_logada(request: Request, call_next):
    path = request.url.path

    public_prefixes = (
        "/login",
        "/static",
        "/health",
        "/api",
        "/docs",
        "/openapi.json",
    )

    if path == "/" or path.startswith(public_prefixes):
        return await call_next(request)


    # V15: vendedor com mais de uma empresa precisa escolher a empresa antes de operar.
    protected_company_paths = (
        "/painel", "/pedidos", "/clientes", "/produtos", "/transportadoras", "/relatorios", "/assistente-pedido"
    )

    db = SessionLocal()
    try:
        current_user = current_user_from_cookie(request, db)
        if not current_user:
            return RedirectResponse(url="/login", status_code=303)
        if path.startswith(protected_company_paths):
            from app.services.company_context_service import get_active_company, get_allowed_companies
            allowed = get_allowed_companies(db, current_user)
            active = get_active_company(request, db, current_user)
            if allowed and not active:
                return RedirectResponse(url="/selecionar-empresa", status_code=303)
    finally:
        db.close()

    return await call_next(request)


app.include_router(web_router)
app.include_router(companies_router)
app.include_router(companies_web_router)
app.include_router(branches_router)
app.include_router(categories_router)
app.include_router(users_router)
app.include_router(users_web_router)
app.include_router(customers_router)
app.include_router(payment_conditions_router)
app.include_router(products_router)
app.include_router(price_tables_router)
app.include_router(orders_router)
app.include_router(carriers_router)
app.include_router(stocks_router)

app.include_router(customers_web_router)
app.include_router(products_web_router)
app.include_router(orders_web_router)
app.include_router(carriers_web_router)
app.include_router(rules_web_router)
app.include_router(assistant_order_web_router)
app.include_router(reports_web_router)
app.include_router(company_context_web_router)
app.include_router(mobile_compat_router)
