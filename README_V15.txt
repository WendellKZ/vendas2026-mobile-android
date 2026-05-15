ERP Vendas 2026 - V15

Login de teste:
Admin: admin@vendas.com / admin123
Representante: rep@vendas.com / 123456

O que foi aplicado na V15:
- Seleção de empresa após login para usuário admin.
- Empresa ativa em sessão: active_company_id.
- Clientes, produtos e pedidos filtrados pela empresa ativa.
- Barra superior mostrando empresa selecionada.
- Pedidos aprovados podem ser reabertos para rascunho.
- Pedidos integrados ficam bloqueados para edição.
- Opção Manter como orçamento ao lado do fluxo de aprovação.
- Prevenção de itens duplicados: soma quantidade se o produto já existe no pedido.
- Reaproveitamento automático do endereço de entrega do cliente.
- Ações rápidas de WhatsApp e e-mail no pedido/cliente.
- Visual premium com cards, botões arredondados, azul degradê e layout responsivo.

Passo 2 - Rodar localmente:
1. Extraia o zip.
2. Abra o PowerShell na pasta extraída.
3. Execute:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python run.py
4. Acesse:
   http://127.0.0.1:5000

Passo 3 - Testar:
- Entre como admin.
- Selecione uma empresa.
- Cadastre cliente/produto.
- Crie pedido.
- Adicione produto repetido para validar soma de quantidade.
- Envie para aprovação.
- Aprove e depois teste reabrir aprovado.
- Marque como integrado e confirme que edição fica bloqueada.

Passo 4 - Render:
Build command: pip install -r requirements.txt
Start command: gunicorn wsgi:app
