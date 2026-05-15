V36 - Confirmação real de pedido no ERP Render

Problema tratado:
- O app informava que o pedido foi enviado, mas ele não aparecia no ERP Web.

Correções no app:
- Depois do POST /api/mobile/pedidos, o app consulta novamente GET /api/mobile/pedidos.
- O app só mostra “confirmado no ERP Web” se o pedido criado voltar na consulta online.
- Se o ERP responder mas o pedido não aparecer na listagem, o app salva o pedido em pendências para sincronizar depois. Assim evitamos falso positivo.

Patch do ERP:
- Arquivo: backend_patch_fastapi/mobile_compat_v36.py
- Melhorado o cadastro/seleção de cliente para não usar o primeiro cliente aleatório do banco.
- Pedido passa a retornar confirmado_erp, vendedor e dica de filtro no Web.

Atenção:
- Se o pedido foi feito com o usuário Samir, no ERP Web confirme se você está vendo a mesma empresa e o mesmo vendedor/filtro.
- Se o Render ainda estiver com o backend antigo, envie o patch do ERP para o repositório do ERP Web e faça novo deploy.
