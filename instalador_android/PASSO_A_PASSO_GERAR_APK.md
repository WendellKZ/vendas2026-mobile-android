# Passo a passo para gerar o instalador APK

## 1. Abrir o projeto

Abra o Android Studio e selecione a pasta do projeto V22.

## 2. Conferir o dispositivo

Você pode gerar APK mesmo sem celular conectado. Para testar antes, use o emulador Pixel 6.

## 3. Gerar APK de teste

No menu superior:

```text
Build > Build Bundle(s) / APK(s) > Build APK(s)
```

Quando aparecer a mensagem de sucesso, clique em:

```text
locate
```

O arquivo normalmente estará em:

```text
app/build/outputs/apk/debug/app-debug.apk
```

## 4. Renomear o APK

Você pode renomear para:

```text
Vendas2026Mobile_V22.apk
```

## 5. Instalar no celular Android

Copie o APK para o celular, toque nele e instale.

Se aparecer bloqueio de segurança, libere:

```text
Configurações > Segurança > Instalar apps desconhecidos
```

## 6. Login de teste

```text
admin
123
```

## 7. Para gerar versão de produção futuramente

Use:

```text
Build > Generate Signed Bundle / APK
```

Para Play Store, prefira `.aab`.
Para instalação manual, use `.apk`.
