ERP Vendas 2026 - V15 Final Aplicada

Login de teste:
- Admin: admin@lider.com / admin123
- Vendedor: vendedor@lider.com / 123456

Como rodar localmente:
1. Extraia o ZIP.
2. Abra o PowerShell dentro da pasta erp_vendas_completo.
3. Rode:
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   py -3.12 -m uvicorn app.main:app --reload --port 5098
4. Acesse:
   http://127.0.0.1:5098

O que foi aplicado/corrigido:
- Correção definitiva da rota /static para CSS/JS no FastAPI.
- Base HTML corrigida para FastAPI/Jinja2, sem chamadas Flask incompatíveis.
- Seleção de empresa ativa após login.
- Cookie active_company_id para manter a empresa ativa.
- Barra superior exibindo empresa ativa.
- Troca rápida de empresa quando o usuário tiver mais de uma empresa.
- Auto-migração para company_id em clientes, produtos e pedidos.
- Empresa padrão criada automaticamente para bancos antigos.
- Vínculo automático dos usuários à empresa padrão.
- Clientes, produtos e pedidos filtrados pela empresa ativa nas telas principais.
- Pedidos aprovados continuam editáveis/reabertos; integrados ficam bloqueados.
- Fluxo de conferência antes de integrar ao ERP.
- Ações WhatsApp/e-mail mantidas.
- Prevenção de item duplicado no carrinho mantida.

Render:
Build command: pip install -r requirements.txt
Start command: gunicorn wsgi:app -k uvicorn.workers.UvicornWorker
