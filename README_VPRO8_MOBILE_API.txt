V-PRO 8 — API MOBILE OFFLINE-FIRST
==================================

Esta versão prepara o sistema Web para receber um app Android offline.
Ela NÃO é o app ainda. É a base correta para o app baixar dados e enviar pedidos.

NOVOS ENDPOINTS
---------------
1) Login mobile
POST /mobile/login
Body JSON:
{
  "email": "vendedor@lider.com",
  "password": "123456"
}

Retorna um token Bearer para usar nas próximas chamadas.

2) Carga inicial para o app
GET /mobile/sync/bootstrap
Header:
Authorization: Bearer SEU_TOKEN

Retorna:
- clientes
- produtos
- transportadoras
- condições de pagamento
- regras comerciais
- dados do vendedor

3) Enviar pedido offline para a Web
POST /mobile/pedidos/sync
Header:
Authorization: Bearer SEU_TOKEN
Body exemplo:
{
  "mobile_uuid": "pedido-local-001",
  "customer_id": 1,
  "carrier_id": 1,
  "payment_condition": "28 dias",
  "delivery_location": "Entrega padrão",
  "freight_value": 0,
  "items": [
    {"product_id": 1, "quantity": 10, "discount": 0}
  ]
}

4) Consultar status dos pedidos sincronizados
GET /mobile/pedidos/status
Header:
Authorization: Bearer SEU_TOKEN

PASSO A PASSO
-------------
Passo 2: extraia e substitua a pasta anterior.
Passo 3: rode iniciar_local_5098.bat.
Passo 4: acesse http://localhost:5098 para validar a Web.
Passo 5: acesse http://localhost:5098/docs para testar os endpoints /mobile.

OBSERVAÇÃO IMPORTANTE
---------------------
O campo mobile_uuid evita pedido duplicado. Se o app tentar reenviar o mesmo pedido,
a Web responde que ele já foi sincronizado.

PRÓXIMA ETAPA
-------------
V9 — App Android MVP com React Native/Expo, SQLite local e sincronização inicial.
