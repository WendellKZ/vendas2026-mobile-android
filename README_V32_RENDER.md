# Vendas 2026 Mobile - V32 Render Online

Esta versão foi ajustada para uso online com ERP publicado no Render.

## Onde alterar a URL do ERP

Abra o arquivo:

```text
app/src/main/java/com/vendas2026/mobile/data/AppConfig.kt
```

Troque esta linha:

```kotlin
const val DEFAULT_API_BASE_URL = "https://COLE-AQUI-A-URL-DO-SEU-ERP.onrender.com"
```

pela URL real do seu ERP no Render, exemplo:

```kotlin
const val DEFAULT_API_BASE_URL = "https://vendas2026-erp.onrender.com"
```

Não coloque barra no final e não coloque porta 5098.

## Teste antes no navegador

```text
https://SEU-ERP.onrender.com/api/mobile/ping
```

## Gerar APK

No Android Studio:

```text
Build > Build Bundle(s) / APK(s) > Build APK(s)
```

## Login

```text
admin
123
```
