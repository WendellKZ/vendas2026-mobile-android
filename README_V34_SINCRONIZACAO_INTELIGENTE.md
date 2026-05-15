# V34 - Sincronização Inteligente ERP ↔ Mobile

## O que mudou

- Corrigida a tela Offline que tinha dois botões **Voltar**.
- Novo botão principal: **Sincronizar agora**.
- A sincronização agora tenta fazer duas coisas:
  - Enviar pedidos pendentes criados offline.
  - Receber atualizações do ERP: pedidos/status, produtos, clientes, transportadoras e condições de pagamento.
- Feedback visual após sincronizar:
  - Quantos pedidos foram enviados.
  - Quantas atualizações foram recebidas.
  - Se houve alguma pendência.

## URL do ERP

A URL padrão foi deixada em:

```kotlin
https://erp-vendas-vpro.onrender.com
```

Caso precise alterar, edite:

```text
app/src/main/java/com/vendas2026/mobile/data/AppConfig.kt
```

## Como gerar APK

No Android Studio:

```text
Build > Build Bundle(s) / APK(s) > Build APK(s)
```

