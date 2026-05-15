# Vendas 2026 Mobile - V33

Versão focada em produtividade do representante.

## Novidades

- Compartilhar pedido por WhatsApp/compartilhamento do Android.
- Geração de PDF simples do pedido para envio.
- Modo offline com fila de pedidos pendentes.
- Tela de sincronização manual.
- Status em tempo real via atualização da carteira de pedidos.
- Assinatura do cliente direto na tela do celular.
- Mantida integração online com ERP Web no Render.

## Antes de gerar APK

Edite o arquivo:

```text
app/src/main/java/com/vendas2026/mobile/data/AppConfig.kt
```

Troque:

```kotlin
https://COLE-AQUI-A-URL-DO-SEU-ERP.onrender.com
```

pela URL real do ERP no Render, sem barra no final.

Exemplo:

```kotlin
https://vendas2026-erp.onrender.com
```

## Gerar APK

No Android Studio:

```text
Build > Build Bundle(s) / APK(s) > Build APK(s)
```

Depois clique em `locate` e instale o APK no celular.
