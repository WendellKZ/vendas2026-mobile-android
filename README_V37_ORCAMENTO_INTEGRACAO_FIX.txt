V37 - Orçamento e integração corrigidos

Ajustes aplicados:
- Mantido botão Manter como orçamento no carrinho.
- Botão Enviar para aprovação agora envia tipo_finalizacao=APROVACAO.
- Orçamento envia tipo_finalizacao=ORCAMENTO.
- Payload do pedido inclui acao, status_solicitado e manter_orcamento.
- App só confirma sucesso após validar resposta/consulta do ERP.

Antes de gerar o APK:
1. Conferir app/src/main/java/com/vendas2026/mobile/data/AppConfig.kt
2. Confirmar DEFAULT_API_BASE_URL = https://erp-vendas-vpro.onrender.com
3. Sync Project with Gradle Files
4. Build > Build Bundle(s) / APK(s) > Build APK(s)
