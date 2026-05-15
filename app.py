import os
from datetime import datetime
from functools import wraps
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vendas2026-v15-dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///erp_vendas_v15.db').replace('postgres://','postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    trade_name = db.Column(db.String(120), nullable=True)
    cnpj = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default='vendedor')
    active = db.Column(db.Boolean, default=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    company = db.relationship('Company')
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    document = db.Column(db.String(30), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    state = db.Column(db.String(2), nullable=True)
    email = db.Column(db.String(160), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    delivery_address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    company = db.relationship('Company')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    sku = db.Column(db.String(60), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    price = db.Column(db.Numeric(12,2), default=0)
    stock = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    company = db.relationship('Company')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(30), default='rascunho')
    delivery_address = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    company = db.relationship('Company')
    client = db.relationship('Client')
    user = db.relationship('User')
    items = db.relationship('OrderItem', cascade='all, delete-orphan', backref='order')
    @property
    def total(self): return sum([float(i.quantity) * float(i.unit_price) for i in self.items])

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(12,2), default=0)
    product = db.relationship('Product')

STATUS_LABELS = {
    'rascunho':'Rascunho','orcamento':'Orçamento','em_aprovacao':'Em aprovação',
    'aprovado':'Aprovado','integrado':'Integrado','cancelado':'Cancelado'
}

def money(v):
    return f"R$ {float(v or 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X','.')
app.jinja_env.filters['money'] = money

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper

def active_company():
    cid = session.get('active_company_id')
    return Company.query.get(cid) if cid else None

@app.context_processor
def inject_globals():
    return {'active_company': active_company(), 'status_labels': STATUS_LABELS}

@app.before_request
def ensure_seed():
    db.create_all()
    if not Company.query.first():
        c1 = Company(name='Grupo Líder', trade_name='Líder Brinquedos', cnpj='00.000.000/0001-00')
        c2 = Company(name='Apolo Brinquedos', trade_name='Apolo', cnpj='00.000.000/0002-00')
        db.session.add_all([c1,c2]); db.session.flush()
        admin = User(name='Administrador', email='admin@vendas.com', role='admin', company_id=None)
        admin.set_password('admin123')
        rep = User(name='Representante Demo', email='rep@vendas.com', role='vendedor', company_id=c1.id)
        rep.set_password('123456')
        db.session.add_all([admin, rep]); db.session.flush()
        for c in [c1,c2]:
            db.session.add_all([
                Client(company_id=c.id, name='Cliente Premium '+c.trade_name, document='12.345.678/0001-90', city='São Paulo', state='SP', email='compras@cliente.com', phone='11999999999', delivery_address='Rua Comercial, 100 - São Paulo/SP'),
                Client(company_id=c.id, name='Loja Exemplo '+c.trade_name, document='98.765.432/0001-10', city='Santo André', state='SP', email='loja@exemplo.com', phone='11888888888', delivery_address='Av. Central, 250 - Santo André/SP'),
                Product(company_id=c.id, sku='BONECO-001', name='Boneco Colecionável Premium', category='Colecionáveis', price=59.90, stock=120),
                Product(company_id=c.id, sku='KIT-002', name='Kit Infantil Venda Rápida', category='Kits', price=129.90, stock=80),
                Product(company_id=c.id, sku='PROMO-003', name='Produto Campanha PDV', category='Campanha', price=39.90, stock=200),
            ])
        db.session.commit()

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email','').strip().lower(), active=True).first()
        if user and user.check_password(request.form.get('password','')):
            session.clear(); session['user_id']=user.id; session['user_name']=user.name; session['role']=user.role
            if user.company_id and user.role != 'admin':
                session['active_company_id'] = user.company_id
                return redirect(url_for('dashboard'))
            return redirect(url_for('select_company'))
        flash('E-mail ou senha inválidos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/empresas', methods=['GET','POST'])
@login_required
def select_company():
    user = User.query.get(session['user_id'])
    companies = Company.query.filter_by(active=True).all() if user.role == 'admin' else Company.query.filter_by(id=user.company_id, active=True).all()
    if request.method == 'POST':
        cid = int(request.form.get('company_id'))
        if any(c.id == cid for c in companies):
            session['active_company_id'] = cid
            flash('Empresa ativa alterada com sucesso.', 'success')
            return redirect(url_for('dashboard'))
    return render_template('select_company.html', companies=companies)

@app.route('/')
@login_required
def dashboard():
    if not active_company(): return redirect(url_for('select_company'))
    cid = session['active_company_id']
    stats = {
        'clients': Client.query.filter_by(company_id=cid).count(),
        'products': Product.query.filter_by(company_id=cid, active=True).count(),
        'orders': Order.query.filter_by(company_id=cid).count(),
        'approved': Order.query.filter_by(company_id=cid, status='aprovado').count(),
    }
    recent_orders = Order.query.filter_by(company_id=cid).order_by(Order.updated_at.desc()).limit(6).all()
    return render_template('dashboard.html', stats=stats, recent_orders=recent_orders)

@app.route('/clientes', methods=['GET','POST'])
@login_required
def clients():
    if not active_company(): return redirect(url_for('select_company'))
    cid = session['active_company_id']
    if request.method == 'POST':
        db.session.add(Client(company_id=cid, name=request.form['name'], document=request.form.get('document'), city=request.form.get('city'), state=request.form.get('state'), email=request.form.get('email'), phone=request.form.get('phone'), delivery_address=request.form.get('delivery_address')))
        db.session.commit(); flash('Cliente cadastrado.', 'success'); return redirect(url_for('clients'))
    q = request.args.get('q','')
    query = Client.query.filter_by(company_id=cid)
    if q: query = query.filter(Client.name.ilike(f'%{q}%'))
    return render_template('clients.html', clients=query.order_by(Client.name).all())

@app.route('/produtos', methods=['GET','POST'])
@login_required
def products():
    if not active_company(): return redirect(url_for('select_company'))
    cid = session['active_company_id']
    if request.method == 'POST':
        price = Decimal((request.form.get('price') or '0').replace(',','.'))
        db.session.add(Product(company_id=cid, sku=request.form['sku'], name=request.form['name'], category=request.form.get('category'), price=price, stock=int(request.form.get('stock') or 0)))
        db.session.commit(); flash('Produto cadastrado.', 'success'); return redirect(url_for('products'))
    q = request.args.get('q','')
    query = Product.query.filter_by(company_id=cid, active=True)
    if q: query = query.filter((Product.name.ilike(f'%{q}%')) | (Product.sku.ilike(f'%{q}%')))
    return render_template('products.html', products=query.order_by(Product.name).all())

@app.route('/pedidos')
@login_required
def orders():
    if not active_company(): return redirect(url_for('select_company'))
    cid=session['active_company_id']; status=request.args.get('status','')
    query=Order.query.filter_by(company_id=cid)
    if status: query=query.filter_by(status=status)
    return render_template('orders.html', orders=query.order_by(Order.updated_at.desc()).all())

@app.route('/pedidos/novo', methods=['GET','POST'])
@login_required
def order_new():
    if not active_company(): return redirect(url_for('select_company'))
    cid=session['active_company_id']
    if request.method == 'POST':
        client = Client.query.filter_by(id=request.form['client_id'], company_id=cid).first_or_404()
        order=Order(company_id=cid, client_id=client.id, user_id=session['user_id'], delivery_address=request.form.get('delivery_address') or client.delivery_address, notes=request.form.get('notes'))
        db.session.add(order); db.session.commit()
        flash('Pedido criado. Agora adicione os produtos.', 'success')
        return redirect(url_for('order_edit', order_id=order.id))
    return render_template('order_form.html', clients=Client.query.filter_by(company_id=cid).order_by(Client.name).all())

@app.route('/pedidos/<int:order_id>', methods=['GET','POST'])
@login_required
def order_edit(order_id):
    if not active_company(): return redirect(url_for('select_company'))
    cid=session['active_company_id']
    order=Order.query.filter_by(id=order_id, company_id=cid).first_or_404()
    if request.method == 'POST':
        if order.status == 'integrado':
            flash('Pedido integrado não pode ser editado.', 'warning'); return redirect(url_for('order_edit', order_id=order.id))
        product=Product.query.filter_by(id=request.form['product_id'], company_id=cid, active=True).first_or_404()
        qty=max(1, int(request.form.get('quantity') or 1))
        existing=OrderItem.query.filter_by(order_id=order.id, product_id=product.id).first()
        if existing:
            existing.quantity += qty
            flash('Produto já existia no pedido. Quantidade somada para evitar duplicidade.', 'info')
        else:
            db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=qty, unit_price=product.price))
        db.session.commit(); return redirect(url_for('order_edit', order_id=order.id))
    products=Product.query.filter_by(company_id=cid, active=True).order_by(Product.name).all()
    return render_template('order_edit.html', order=order, products=products)

@app.route('/pedidos/<int:order_id>/item/<int:item_id>/remover', methods=['POST'])
@login_required
def order_item_remove(order_id,item_id):
    order=Order.query.filter_by(id=order_id, company_id=session.get('active_company_id')).first_or_404()
    if order.status == 'integrado': flash('Pedido integrado não pode ser alterado.', 'warning')
    else:
        item=OrderItem.query.filter_by(id=item_id, order_id=order.id).first_or_404(); db.session.delete(item); db.session.commit(); flash('Item removido.', 'success')
    return redirect(url_for('order_edit', order_id=order.id))

@app.route('/pedidos/<int:order_id>/status/<status>', methods=['POST'])
@login_required
def order_status(order_id,status):
    order=Order.query.filter_by(id=order_id, company_id=session.get('active_company_id')).first_or_404()
    if order.status == 'integrado':
        flash('Pedido integrado está bloqueado para alterações.', 'warning')
    elif status in STATUS_LABELS:
        order.status=status; db.session.commit(); flash('Status atualizado.', 'success')
    return redirect(url_for('order_edit', order_id=order.id))

@app.route('/pedidos/<int:order_id>/reabrir', methods=['POST'])
@login_required
def order_reopen(order_id):
    order=Order.query.filter_by(id=order_id, company_id=session.get('active_company_id')).first_or_404()
    if order.status == 'aprovado':
        order.status='rascunho'; db.session.commit(); flash('Pedido aprovado reaberto para edição.', 'success')
    else:
        flash('Somente pedidos aprovados podem ser reabertos. Integrados continuam bloqueados.', 'warning')
    return redirect(url_for('order_edit', order_id=order.id))

@app.route('/api/clientes/<int:client_id>/endereco')
@login_required
def client_address(client_id):
    client=Client.query.filter_by(id=client_id, company_id=session.get('active_company_id')).first_or_404()
    return jsonify({'delivery_address': client.delivery_address or ''})

if __name__ == '__main__':
    app.run(debug=True)
