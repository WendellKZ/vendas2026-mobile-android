# Patch Flask - API Mobile Vendas 2026 V7

## Objetivo

Permitir que o app Android envie pedidos para o ERP Web por API, sem mexer nas tabelas atuais do sistema.

Nesta V7, por segurança, os pedidos do app são gravados em um banco SQLite separado:

```text
mobile_pedidos.db
```

Assim testamos a integração real App → Web sem risco para o ERP atual.

## Passo 2 - Aplicar no ERP Web

1. Copie o arquivo:

```text
backend_patch_flask/mobile_api.py
```

para a raiz do seu ERP Flask, ao lado do `app.py` ou `run.py`.

2. No arquivo onde o Flask cria o `app`, adicione depois da criação do app:

```python
from mobile_api import mobile_api
app.register_blueprint(mobile_api)
```

Exemplo:

```python
app = Flask(__name__)

from mobile_api import mobile_api
app.register_blueprint(mobile_api)
```

3. Rode o ERP localmente:

```powershell
python app.py
```

ou:

```powershell
flask run
```

## Passo 3 - Validar no navegador

Abra:

```text
http://localhost:5098/api/mobile/pedidos
```

E também:

```text
http://localhost:5098/mobile/pedidos
```

## Passo 4 - Ligar o app Android na API

No Android Studio, abra:

```text
app/src/main/java/com/vendas2026/mobile/data/AppConfig.kt
```

Altere:

```kotlin
const val MOCK_MODE = true
```

para:

```kotlin
const val MOCK_MODE = false
```

No emulador Android, use:

```kotlin
const val API_BASE_URL = "http://10.0.2.2:5098"
```

## Passo 5 - Testar

1. Rode o ERP Web.
2. Rode o app no Android Studio.
3. Faça login no app.
4. Crie um pedido.
5. Abra no navegador:

```text
http://localhost:5098/mobile/pedidos
```

O pedido criado no app deve aparecer nessa tela Web.

## Próxima V7

Na V7, trocaremos a função `salvar_pedido_mobile()` para gravar diretamente nas tabelas reais do ERP Web.
