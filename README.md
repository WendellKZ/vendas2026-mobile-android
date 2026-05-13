# App Android Vendas 2026 - V26 Integração Web

Versão focada em deixar o app mais funcional para representantes e preparar o pedido para aparecer no ERP Web.

## O que mudou nesta V26

- Removida a aba/card **Segurança** do menu.
- Mantido o card **Empresa** para troca de empresa ativa.
- App configurado com `MOCK_MODE=false` para enviar pedidos pela API do ERP Web.
- Pedido criado no app é enviado para `POST /api/mobile/pedidos`.
- Patch Flask incluso em `backend_patch_flask/mobile_api.py` para consultar pedidos em `/mobile/pedidos`.

## Login de teste

Com o patch Flask aplicado, o login aceita usuário e senha para teste:

```text
admin
123
```

## Passo 2 - Aplicar a API no ERP Web

1. Copie `backend_patch_flask/mobile_api.py` para a raiz do ERP Web, ao lado do `app.py` ou `run.py`.
2. No arquivo principal Flask, depois de criar o `app`, adicione:

```python
from mobile_api import mobile_api
app.register_blueprint(mobile_api)
```

3. Rode o ERP Web localmente.
4. Teste no navegador:

```text
http://localhost:5098/mobile/pedidos
```

## Passo 3 - Rodar no Android Studio

No emulador Android, a URL padrão já está configurada como:

```text
http://10.0.2.2:5098
```

Se for testar em celular físico, altere em:

```text
app/src/main/java/com/vendas2026/mobile/data/AppConfig.kt
```

Troque `API_BASE_URL` pelo IP do seu computador na rede, por exemplo:

```kotlin
const val API_BASE_URL = "http://192.168.0.50:5098"
```

## Passo 4 - Validar pedido integrado

1. Abra o app.
2. Faça login.
3. Selecione a empresa.
4. Crie um pedido.
5. Finalize o carrinho.
6. No ERP Web, abra:

```text
http://localhost:5098/mobile/pedidos
```

O pedido criado no app deve aparecer nessa tela.


## V27 - Ajuste para FastAPI/Uvicorn

Esta versão foi ajustada para o seu ERP Web rodando com:

```powershell
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --reload --port 5098
```

No emulador Android, a API fica configurada como:

```text
http://10.0.2.2:5098
```

Se for testar em celular físico, troque em `AppConfig.kt` para o IP do computador, exemplo:

```kotlin
const val API_BASE_URL = "http://192.168.0.105:5098"
```



## V30 - Configuração do servidor no celular físico

Esta versão mostra o servidor atual já na tela de login e traz o botão **Alterar servidor / IP do ERP**.

Para celular físico, não use `10.0.2.2`. Use o IPv4 do computador na rede Wi-Fi, por exemplo:

```text
http://192.168.0.105:5098
```

O ERP deve estar rodando com:

```powershell
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --reload --port 5098
```

Teste no celular pelo navegador:

```text
http://IP_DO_PC:5098/api/mobile/ping
```
