# Correção SQLAlchemy - PaymentCondition.orders

## Problema corrigido

Erro:

```text
Could not determine join condition between parent/child tables on relationship PaymentCondition.orders
```

Isso acontece porque o model `PaymentCondition` possui um relacionamento com `Order`, mas a tabela `orders` não possui uma chave estrangeira para `payment_conditions`.

## Correção aplicada

O script remove/comenta somente o relacionamento quebrado:

```python
orders = relationship("Order", back_populates="payment_condition")
```

Isso libera o sistema para subir normalmente sem alterar o fluxo atual de pedidos.

## Como aplicar

### 2. Copiar arquivos

Extraia este ZIP dentro de:

```text
C:\erp_vendas_completo
```

Deixe a pasta `scripts` dentro do projeto.

### 3. Rodar a correção

No PowerShell:

```powershell
cd C:\erp_vendas_completo
.\corrigir_payment_condition.ps1
```

## Alternativa manual

Se o PowerShell bloquear execução:

```powershell
cd C:\erp_vendas_completo
python .\scripts\corrigir_payment_condition.py
docker compose down
docker compose up -d --build
```

## Testar

```text
http://localhost:5098/painel
http://localhost:5098/pedidos
```
