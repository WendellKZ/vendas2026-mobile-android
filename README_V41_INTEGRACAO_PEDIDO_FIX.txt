V41 - Correção de integração de pedido App Android -> ERP Web

O que foi ajustado:
- Envio do pedido com mobile_uuid para rastreio.
- Payload ampliado com campos compatíveis com endpoints antigos e novos do ERP.
- Itens enviados com codigo_produto, sku, code, product_id, quantidade, quantity, desconto e total.
- O app agora considera integrado quando o ERP responde HTTP 2xx com número/id do pedido.
- A consulta posterior de pedidos continua sendo feita, mas não bloqueia o sucesso por causa de filtro de empresa/vendedor.

Importante:
- O ERP no Render precisa estar com a rota /api/mobile/pedidos ativa.
- Depois de subir esta versão no GitHub/Android Studio, gere um APK novo.
- Após enviar um pedido, confira no ERP em Pedidos e também revise filtros de empresa/vendedor/status.
